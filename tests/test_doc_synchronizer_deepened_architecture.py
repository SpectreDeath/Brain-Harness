"""
Deepened Architecture Verification Suite for DocSynchronizer.

Verifies:
1. Micro-Kernel Seam Elevation & IoC Container Resolution (AGENTS.md Rule 49, Rule 45)
2. PluginValidator & Manifest Contract Compliance (AGENTS.md Rule 34, Rule 38)
3. In-Memory Operation execution without CLI Subprocess Forks (Rule 49)
4. Code-to-Doc AST Symbol Drift Detection (broken classes, functions, methods)
5. Incremental mtime-Indexed AST Cache Performance
6. Top-Level Tool Entrypoint Function Contracts
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.doc_synchronizer import (
    DOC_SYNCHRONIZER_SERVICE_KEY,
    DocCoverageReportData,
    DocDriftReportData,
    DocSynchronizerService,
)
from plugins.developer_tooling.doc_synchronizer.main import (
    DocSynchronizerPlugin,
    doc_audit,
    doc_drift_check,
    doc_scaffold,
    doc_visual_brief,
    plugin,
)

PLUGIN_DIR = (
    Path(__file__).resolve().parent.parent
    / "plugins"
    / "developer_tooling"
    / "doc_synchronizer"
)


@pytest.mark.unit
class TestDocSynchronizerPluginRegistration:
    """Verifies IoC container integration and plugin manifest conformity."""

    @pytest.mark.asyncio
    async def test_plugin_implements_protocol_and_registers_ioc(self) -> None:
        """DocSynchronizerPlugin satisfies DocSynchronizerService and resolves via ServiceKey."""
        assert isinstance(plugin, DocSynchronizerService)
        assert plugin.name == "plugin.doc_synchronizer"
        assert plugin.provides == [DOC_SYNCHRONIZER_SERVICE_KEY]
        assert plugin.requires == []

        ctx = ServiceContext()
        await plugin.on_load(ctx)

        resolved = ctx.require(DOC_SYNCHRONIZER_SERVICE_KEY)
        assert resolved is plugin

    def test_plugin_manifest_validation(self) -> None:
        """Plugin manifest complies with PluginValidator standards (Rule 34, Rule 38)."""
        report = PluginValidator.validate_sync(PLUGIN_DIR)
        assert report.valid is True, f"Plugin validation failed: {report.errors}"


@pytest.mark.unit
class TestInMemoryDocOperations:
    """Verifies in-memory audit, scaffolding, and visual brief execution without subprocesses."""

    @pytest.fixture
    def workspace(self, tmp_path: Path) -> Path:
        """Constructs an isolated workspace with modules and documentation."""
        src_dir = tmp_path / "src" / "sample_pkg"
        src_dir.mkdir(parents=True, exist_ok=True)

        mod_a = src_dir / "worker.py"
        mod_a.write_text(
            '"""Background task worker."""\n\n'
            "class TaskWorker:\n"
            '    """Executes asynchronous queued jobs."""\n'
            "    def execute(self, task_id: str) -> bool:\n"
            '        """Execute task."""\n'
            "        return True\n",
            encoding="utf-8",
        )

        mod_b = src_dir / "utils.py"
        mod_b.write_text(
            "def format_task(task_id: str) -> str:\n"
            '    """Format a task ID."""\n'
            '    return f"task:{task_id}"\n',
            encoding="utf-8",
        )

        readme = src_dir / "README.md"
        readme.write_text(
            "# Sample Package\n\nSee [Worker](worker.py) for details.\n",
            encoding="utf-8",
        )

        return tmp_path

    def test_in_memory_audit_returns_typed_report(self, workspace: Path) -> None:
        """Audit runs in-process and returns typed DocCoverageReportData."""
        local_plugin = DocSynchronizerPlugin(root_dir=workspace)
        report = local_plugin.audit(target_dir=workspace / "src")

        assert isinstance(report, DocCoverageReportData)
        assert report.total_modules == 2
        assert report.modules_with_docstring == 1
        assert report.total_symbols >= 2
        assert len(report.modules) == 2

    def test_in_memory_scaffolding(self, workspace: Path) -> None:
        """Scaffold generates Diataxis markdown using live AST inspection."""
        local_plugin = DocSynchronizerPlugin(root_dir=workspace)
        target_mod = workspace / "src" / "sample_pkg" / "worker.py"
        out_doc = workspace / "worker_api.md"

        res = local_plugin.scaffold(
            module_path=target_mod,
            doc_type="api",
            output_path=out_doc,
        )

        assert res.exists()
        assert res == out_doc
        text = out_doc.read_text(encoding="utf-8")
        assert "worker API Reference" in text
        assert "class TaskWorker" in text
        assert "def execute" in text

    def test_in_memory_visual_brief(self, workspace: Path) -> None:
        """Visual brief generates HTML with dark-mode styling and Mermaid diagram."""
        local_plugin = DocSynchronizerPlugin(root_dir=workspace)
        out_html = workspace / "coverage_brief.html"

        res = local_plugin.visual_brief(
            target_dir=workspace / "src",
            output_path=out_html,
        )

        assert res.exists()
        assert res == out_html
        content = out_html.read_text(encoding="utf-8")
        assert "Documentation Coverage Brief & Scorecard" in content
        assert "mermaid" in content


@pytest.mark.unit
class TestCodeToDocSymbolDrift:
    """Verifies AST-based code-to-doc symbol drift verification."""

    @pytest.fixture
    def drift_workspace(self, tmp_path: Path) -> tuple[Path, Path, Path]:
        """Creates a module and documentation containing valid and stale symbol references."""
        pkg = tmp_path / "service"
        pkg.mkdir(parents=True, exist_ok=True)
        docs = tmp_path / "docs"
        docs.mkdir(parents=True, exist_ok=True)

        py_mod = pkg / "engine.py"
        py_mod.write_text(
            '"""Execution engine."""\n\n'
            "class ExecutionEngine:\n"
            '    """Engine."""\n'
            "    def start(self) -> None:\n"
            '        """Start."""\n'
            "        pass\n"
            "    def shutdown(self) -> None:\n"
            '        """Shutdown."""\n'
            "        pass\n",
            encoding="utf-8",
        )

        doc_file = docs / "engine_api.md"
        doc_content = (
            "# Engine Reference\n\n"
            "Referenced module: [Engine](../service/engine.py)\n\n"
            "Valid symbol references:\n"
            "### `class ExecutionEngine`\n"
            "- `def start()`\n"
            "- `def shutdown()`\n\n"
            "Stale symbol references (code drift):\n"
            "### `class ObsoleteEngine`\n"
            "- `def deprecated_method()`\n"
            "- `ExecutionEngine.missing_action()`\n"
        )
        doc_file.write_text(doc_content, encoding="utf-8")

        return tmp_path, docs, doc_file

    def test_drift_check_detects_stale_ast_symbols(
        self, drift_workspace: tuple[Path, Path, Path]
    ) -> None:
        """Drift check flags stale classes, methods, and qualified calls when check_symbols=True."""
        tmp_path, docs, _ = drift_workspace
        local_plugin = DocSynchronizerPlugin(root_dir=tmp_path)

        report = local_plugin.drift_check(docs_dir=docs, check_symbols=True)

        assert isinstance(report, DocDriftReportData)
        assert report.has_drift is True
        assert len(report.stale_symbols) == 3

        stale_names = {s.symbol_name for s in report.stale_symbols}
        assert "ObsoleteEngine" in stale_names
        assert "deprecated_method" in stale_names
        assert "ExecutionEngine.missing_action" in stale_names

    def test_drift_check_ignores_symbols_when_disabled(
        self, drift_workspace: tuple[Path, Path, Path]
    ) -> None:
        """Drift check only verifies links when check_symbols=False."""
        tmp_path, docs, _ = drift_workspace
        local_plugin = DocSynchronizerPlugin(root_dir=tmp_path)

        report = local_plugin.drift_check(docs_dir=docs, check_symbols=False)

        assert isinstance(report, DocDriftReportData)
        # All links are valid in this fixture
        assert len(report.broken_links) == 0
        assert len(report.stale_symbols) == 0
        assert report.has_drift is False


@pytest.mark.unit
class TestMtimeAstCachePerformance:
    """Verifies that in-memory AST caching eliminates disk re-parsing overhead."""

    def test_cache_hits_and_invalidation(self, tmp_path: Path) -> None:
        """Second audit reuses cached ASTs; file mutation invalidates only touched entry."""
        src_dir = tmp_path / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        for i in range(5):
            f = src_dir / f"module_{i}.py"
            f.write_text(f'"""Module {i}."""\ndef f_{i}(): pass\n', encoding="utf-8")

        local_plugin = DocSynchronizerPlugin(root_dir=tmp_path)

        # First audit: all 5 must be cache misses
        local_plugin.audit(target_dir=src_dir)
        stats1 = local_plugin.get_cache_stats()
        assert stats1["misses"] == 5
        assert stats1["hits"] == 0
        assert stats1["cached_entries"] == 5

        # Second audit: all 5 must be cache hits
        local_plugin.audit(target_dir=src_dir)
        stats2 = local_plugin.get_cache_stats()
        assert stats2["hits"] == 5
        assert stats2["misses"] == 5

        # Modify module_0 (update mtime and content)
        time.sleep(0.05)
        mod_0 = src_dir / "module_0.py"
        mod_0.write_text(
            '"""Updated module 0."""\ndef f_new(): pass\n', encoding="utf-8"
        )

        # Third audit: 4 hits, 1 new miss
        local_plugin.audit(target_dir=src_dir)
        stats3 = local_plugin.get_cache_stats()
        assert stats3["hits"] == 9  # 5 from pass 2 + 4 from pass 3
        assert stats3["misses"] == 6  # 5 from pass 1 + 1 from pass 3


@pytest.mark.unit
class TestPluginToolEntrypoints:
    """Verifies top-level tool entrypoints matching plugin.json declarations."""

    def test_top_level_tools_callable(self, tmp_path: Path) -> None:
        """Top-level tool functions execute and return standard dictionary or path outputs."""
        mod = tmp_path / "sample.py"
        mod.write_text('"""Sample module."""\ndef run(): pass\n', encoding="utf-8")

        # doc_audit
        audit_res = doc_audit(target=str(tmp_path), min_coverage=50.0)
        assert isinstance(audit_res, dict)
        assert "total_modules" in audit_res
        assert audit_res["total_modules"] >= 1

        # doc_scaffold
        out_doc = tmp_path / "sample_api.md"
        scaffold_res = doc_scaffold(
            module_path=str(mod), doc_type="api", output_path=str(out_doc)
        )
        assert Path(scaffold_res).exists()

        # doc_drift_check
        drift_res = doc_drift_check(docs_dir=str(tmp_path), check_symbols=True)
        assert isinstance(drift_res, dict)
        assert "has_drift" in drift_res

        # doc_visual_brief
        out_brief = tmp_path / "brief.html"
        brief_res = doc_visual_brief(
            target_dir=str(tmp_path), output_path=str(out_brief)
        )
        assert Path(brief_res).exists()
