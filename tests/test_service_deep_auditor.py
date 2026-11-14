"""Contract tests for DeepRepoAuditorService, IoC plugin, and skill CLI script."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services import (
    DEEP_AUDITOR_SERVICE_KEY,
    AxisFinding,
    ComputeDimensionVector,
    DeepRepoAuditorService,
    DefaultDeepRepoAuditorService,
    TopologyNodeSummary,
    VisualBriefPaths,
    resolve_deep_repo_auditor,
)


def _create_sample_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "wrapper" / "sample-repo"
    (repo / ".git").mkdir(parents=True)
    (repo / "pyproject.toml").write_text('[project]\nname = "sample"\n', encoding="utf-8")
    (repo / "src" / "pkg").mkdir(parents=True)
    (repo / "src" / "pkg" / "core.py").write_text("async def run() -> None:\n    pass\n", encoding="utf-8")
    (repo / "tests").mkdir(parents=True)
    (repo / "tests" / "test_core.py").write_text("def test_ok() -> None:\n    assert True\n", encoding="utf-8")
    (repo / ".github" / "workflows").mkdir(parents=True)
    (repo / ".github" / "workflows" / "ci.yml").write_text("name: CI\n", encoding="utf-8")
    (repo / "plugins" / "external" / "noise").mkdir(parents=True)
    (repo / "plugins" / "external" / "noise" / "ignored.py").write_text(
        "async def ignored() -> None: pass\n", encoding="utf-8"
    )
    return tmp_path / "wrapper"


def test_frozen_slotted_models_enforce_immutability() -> None:
    vec = ComputeDimensionVector(
        ambiguity=0.35,
        span=0.25,
        depth=0.30,
        rigor=0.45,
        concurrency=0.20,
        composite=0.31,
        tier="LOW",
        thinking_budget="LOW_1K",
    )
    finding = AxisFinding(axis="Axis 1", title="Seams", status="PASS", summary="Clean")
    topo = TopologyNodeSummary(
        topology_pattern="Modular Service Package",
        root_manifest="pyproject.toml",
        nesting_depth=1,
        total_files_scanned=4,
        python_files=2,
        plugin_count=0,
        skill_count=0,
        test_file_count=1,
        has_git=True,
    )
    with pytest.raises((AttributeError, TypeError)):
        vec.tier = "HIGH"  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        finding.status = "FAIL"  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        topo.python_files = 99  # type: ignore[misc]


def test_deep_auditor_service_scans_bounded_repo_and_renders_briefs(tmp_path: Path) -> None:
    wrapper_root = _create_sample_repo(tmp_path)
    out_dir = tmp_path / "briefs"
    svc = DefaultDeepRepoAuditorService()

    assert isinstance(svc, DeepRepoAuditorService)
    payload = svc.run_full_audit(wrapper_root, output_dir=out_dir)

    report = payload["report"]
    assert Path(report["resolved_root"]).name == "sample-repo"
    assert report["topology"]["nesting_depth"] == 1
    assert report["topology"]["root_manifest"] == "pyproject.toml"
    assert report["topology"]["python_files"] == 2  # pruned external/noise/ignored.py
    assert len(report["axes"]) == 4

    briefs = VisualBriefPaths(**payload["briefs"])
    assert Path(briefs.compute_brief).is_file()
    assert Path(briefs.topology_brief).is_file()
    assert Path(briefs.repo_reader_brief).is_file()
    assert "5D Compute Vector" in Path(briefs.compute_brief).read_text(encoding="utf-8")
    assert "graph TD" in Path(briefs.topology_brief).read_text(encoding="utf-8")
    assert "4-Axis Introspection Matrix" in Path(briefs.repo_reader_brief).read_text(encoding="utf-8")
    assert len(payload["ki_candidates"]) == 4


@pytest.mark.asyncio
async def test_ioc_plugin_registration_and_validator() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    plugin_dir = repo_root / "plugins" / "software_engineering" / "deep_repo_auditor"

    validation = PluginValidator().validate_sync(plugin_dir)
    assert validation.valid, [f"{c.rule}: {c.message}" for c in validation.checks if not c.passed]

    main_path = plugin_dir / "main.py"
    spec = importlib.util.spec_from_file_location("test_deep_auditor_plugin", main_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    ctx = ServiceContext()
    await mod.plugin.on_load(ctx)
    resolved = resolve_deep_repo_auditor(ctx)
    assert isinstance(resolved, DeepRepoAuditorService)
    assert ctx.require(DEEP_AUDITOR_SERVICE_KEY) is resolved


def test_skill_cli_runner_executes_cleanly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    wrapper_root = _create_sample_repo(tmp_path)
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / ".agents" / "skills" / "deep-repo-auditor" / "scripts" / "run_audit.py"
    spec = importlib.util.spec_from_file_location("test_deep_auditor_cli", script_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    exit_code = mod.main([str(wrapper_root), "--briefs-dir", str(tmp_path / "cli_briefs")])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert '"ki_candidates"' in captured.out
