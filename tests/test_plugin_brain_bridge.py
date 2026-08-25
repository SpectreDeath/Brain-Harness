"""Tests for brain_bridge plugin."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services.brain_bridge import (
    BRAIN_BRIDGE_KEY,
    BrainAttachResult,
    BrainBridgeService,
    BrainDetachResult,
    BrainListResult,
    BrainQueryResult,
)
from plugins.memory_and_epistemics.brain_bridge.main import (
    BrainBridgePlugin,
    _detect_brain_format,
    _index_text_files,
    _is_git_url,
    _parse_git_commits,
    brain_attach,
    brain_detach,
    brain_list_attached,
    brain_query,
)


@pytest.mark.unit
class TestBrainBridgePlugin:
    def test_format_detection(self, tmp_path: Path) -> None:
        # 1. Antigravity Brain
        ag_dir = tmp_path / "ag_brain"
        (ag_dir / ".system_generated" / "logs").mkdir(parents=True)
        (ag_dir / ".system_generated" / "logs" / "transcript.jsonl").write_text("{}\n")
        assert _detect_brain_format(ag_dir) == "antigravity_brain"

        # 2. Harness Instance
        harness_dir = tmp_path / "harness_repo"
        (harness_dir / ".harness").mkdir(parents=True)
        assert _detect_brain_format(harness_dir) == "harness_instance"

        # 3. IDE Memo (Claude / Cursor)
        ide_dir = tmp_path / "ide_repo"
        ide_dir.mkdir()
        (ide_dir / ".cursorrules").write_text("rule content")
        assert _detect_brain_format(ide_dir) == "ide_memo"

        # 4. Obsidian Vault
        vault_dir = tmp_path / "obsidian_vault"
        vault_dir.mkdir()
        (vault_dir / "note.md").write_text("# Knowledge\nSee [[Architecture]] for details.")
        assert _detect_brain_format(vault_dir) == "obsidian_vault"

        # 5. Git Repository via .git folder
        git_dir = tmp_path / "git_repo"
        (git_dir / ".git").mkdir(parents=True)
        assert _detect_brain_format(git_dir) == "git_repository"

        # 6. Code Repository via manifest file
        code_dir = tmp_path / "code_repo"
        code_dir.mkdir()
        (code_dir / "Cargo.toml").write_text("[package]\nname = 'test'")
        assert _detect_brain_format(code_dir) == "git_repository"

        # 7. Raw Docs
        raw_dir = tmp_path / "raw_docs"
        raw_dir.mkdir()
        (raw_dir / "guide.txt").write_text("Plain text documentation.")
        assert _detect_brain_format(raw_dir) == "raw_docs"

    def test_is_git_url(self) -> None:
        assert _is_git_url("https://github.com/owner/repo") is True
        assert _is_git_url("https://github.com/owner/repo.git") is True
        assert _is_git_url("git@github.com:owner/repo.git") is True
        assert _is_git_url("http://gitlab.com/group/proj") is True
        assert _is_git_url("/local/path/to/dir") is False
        assert _is_git_url(r"C:\projects\Brain Harness") is False

    def test_multi_language_indexing(self, tmp_path: Path) -> None:
        repo_dir = tmp_path / "multi_lang_repo"
        repo_dir.mkdir()

        (repo_dir / "app.py").write_text("def run():\n    print('python')\n")
        (repo_dir / "service.ts").write_text("export function serve(): void {\n  console.log('ts');\n}\n")
        (repo_dir / "main.rs").write_text("fn main() {\n    println!(\"rust\");\n}\n")
        (repo_dir / "Dockerfile").write_text("FROM python:3.11\nWORKDIR /app\n")
        (repo_dir / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        chunks, doc_freq, languages, manifests = _index_text_files(repo_dir)

        assert len(chunks) >= 4
        assert "py" in languages
        assert "ts" in languages
        assert "rs" in languages
        assert "pyproject.toml" in manifests
        assert "Dockerfile" in manifests or any("dockerfile" in m.lower() for m in manifests)

    def test_git_repo_attach_and_query(self, tmp_path: Path) -> None:
        repo = tmp_path / "mock_git_repo"
        repo.mkdir()

        # Initialize real git repo
        subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)

        # Create code file and commit
        code_file = repo / "core.py"
        code_file.write_text("class HyperTransformer:\n    def transform(self, data):\n        return data * 2\n")
        subprocess.run(["git", "-C", str(repo), "add", "core.py"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "Implement HyperTransformer core engine"], check=True)

        # Create second file and commit
        manifest = repo / "pyproject.toml"
        manifest.write_text("[project]\nname = 'hyper-transformer'\nversion = '0.1.0'\n")
        subprocess.run(["git", "-C", str(repo), "add", "pyproject.toml"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "Add project manifest and packaging metadata"], check=True)

        # Attach
        attach_res = brain_attach(str(repo), alias="mock_repo")
        assert attach_res["status"] == "ok"
        assert attach_res["alias"] == "mock_repo"
        assert attach_res["detected_format"] == "git_repository"
        assert attach_res["summary"]["git_commit_chunks"] >= 2
        assert "py" in attach_res["summary"]["detected_languages"]

        # Query code
        code_query = brain_query("HyperTransformer transform data", brain_alias="mock_repo")
        assert code_query["status"] == "ok"
        assert code_query["results_count"] >= 1
        assert "core.py" in code_query["results"][0]["file"]

        # Query commit trajectory
        commit_query = brain_query("packaging metadata project manifest", brain_alias="mock_repo")
        assert commit_query["status"] == "ok"
        assert commit_query["results_count"] >= 1
        types = [r["type"] for r in commit_query["results"]]
        assert "git_commit" in types or "document_chunk" in types

        # Detach
        detach_res = brain_detach("mock_repo")
        assert detach_res["status"] == "ok"

    def test_brain_attach_and_query(self, tmp_path: Path) -> None:
        target = tmp_path / "external_brain"
        target.mkdir()

        # Write doc file
        (target / "architecture.md").write_text(
            "# Kernel Design\n"
            "The micro-kernel uses typed ServiceKey[T] and an immutable event bus.\n"
        )

        # Write transcript file
        transcript_line = {
            "step_index": 1,
            "type": "PLANNER_RESPONSE",
            "content": "Refactored topological sorting in plugin dependency manager.",
            "tool_calls": [{"name": "replace_file_content", "args": {}}],
            "status": "DONE",
        }
        (target / "transcript.jsonl").write_text(json.dumps(transcript_line) + "\n")

        # Attach
        attach_res = brain_attach(str(target), alias="test_brain")
        assert attach_res["status"] == "ok"
        assert attach_res["alias"] == "test_brain"
        assert attach_res["summary"]["total_chunks"] >= 2
        assert attach_res["summary"]["trajectories_recorded"] == 1

        # List
        list_res = brain_list_attached()
        assert list_res["status"] == "ok"
        assert list_res["attached_count"] >= 1
        aliases = [b["alias"] for b in list_res["brains"]]
        assert "test_brain" in aliases

        # Query doc
        query_doc = brain_query("ServiceKey micro-kernel architecture", brain_alias="test_brain")
        assert query_doc["status"] == "ok"
        assert query_doc["results_count"] >= 1
        assert "architecture.md" in query_doc["results"][0]["file"]

        # Query transcript trajectory
        query_traj = brain_query("topological sorting dependency manager", brain_alias="test_brain")
        assert query_traj["status"] == "ok"
        assert query_traj["results_count"] >= 1
        assert query_traj["results"][0]["type"] == "transcript_step"

        # Detach
        detach_res = brain_detach("test_brain")
        assert detach_res["status"] == "ok"
        assert detach_res["detached_alias"] == "test_brain"

        # Query after detach
        list_after = brain_list_attached()
        assert "test_brain" not in [b["alias"] for b in list_after["brains"]]

    def test_invalid_path_attach(self) -> None:
        res = brain_attach("/non/existent/path/for/sure")
        assert res["status"] == "error"
        assert "not found" in res["error"].lower()

    @pytest.mark.asyncio
    async def test_brain_bridge_plugin_ioc_lifecycle(self, tmp_path: Path) -> None:
        plugin = BrainBridgePlugin()
        assert plugin.name == "plugin.brain_bridge"
        assert BRAIN_BRIDGE_KEY in plugin.provides

        ctx = ServiceContext()
        await plugin.on_load(ctx)
        await plugin.on_enable()

        service = ctx.require(BRAIN_BRIDGE_KEY)
        assert isinstance(service, BrainBridgeService)

        doc_dir = tmp_path / "ioc_brain"
        doc_dir.mkdir()
        (doc_dir / "readme.md").write_text("# IoC Memory Service\nDeepened memory service architecture.")

        attach_res = await service.attach_async(str(doc_dir), alias="ioc_test")
        assert isinstance(attach_res, BrainAttachResult)
        assert attach_res.status == "ok"

        query_res = await service.query_async("Deepened memory service", brain_alias="ioc_test")
        assert isinstance(query_res, BrainQueryResult)
        assert query_res.status == "ok"
        assert query_res.results_count >= 1

        list_res = service.list_attached()
        assert isinstance(list_res, BrainListResult)
        assert list_res.attached_count >= 1

        detach_res = service.detach("ioc_test")
        assert isinstance(detach_res, BrainDetachResult)
        assert detach_res.status == "ok"

        await plugin.on_disable()
        await plugin.on_unload()
