"""Verification tests for deepened ArchLinterService and consolidated plugin seam."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services import (
    ARCH_LINTER_KEY,
    ArchLinterService,
    BoundaryCheckResult,
    CircularImportResult,
    DefaultArchLinterService,
    FileDiagnostic,
    FileLintResult,
    ModuleCouplingResult,
    resolve_arch_linter,
)
from plugins.software_engineering.arch_linter.main import (
    ArchLinterPlugin,
    compute_module_coupling,
    detect_circular_imports,
    plugin as arch_linter_singleton,
    verify_clean_boundaries,
)


@pytest.mark.unit
def test_lint_file_never_returns_none() -> None:
    """ArchLinterService.lint_file must always return a FileLintResult instance, never None."""
    svc = DefaultArchLinterService()

    # Valid Python
    res_clean = svc.lint_file("clean.py", content="x = 1\n")
    assert res_clean is not None
    assert isinstance(res_clean, FileLintResult)
    assert res_clean.is_clean is True

    # Syntax error Python
    res_syntax = svc.lint_file("broken.py", content="def err(\n")
    assert res_syntax is not None
    assert isinstance(res_syntax, FileLintResult)
    assert res_syntax.is_clean is False

    # Broken JSON
    res_json = svc.lint_file("cfg.json", content="{unquoted: }")
    assert res_json is not None
    assert isinstance(res_json, FileLintResult)
    assert res_json.is_clean is False

    # Unbalanced brackets
    res_brackets = svc.lint_file("code.ts", content="function test() { return (1 + 2;")
    assert res_brackets is not None
    assert isinstance(res_brackets, FileLintResult)
    assert res_brackets.is_clean is False

    # Missing file
    res_missing = svc.lint_file("nonexistent_file_path_12345.py")
    assert res_missing is not None
    assert isinstance(res_missing, FileLintResult)
    assert res_missing.is_clean is False


@pytest.mark.unit
def test_arch_linter_plugin_inherits_lint_file() -> None:
    """ArchLinterPlugin must inherit and provide lint_file returning FileLintResult."""
    plugin = ArchLinterPlugin()
    res = plugin.lint_file("clean.py", content="x = 1\n")
    assert res is not None
    assert isinstance(res, FileLintResult)
    assert res.is_clean is True
    assert res.error_count == 0


@pytest.mark.unit
def test_detect_circular_imports_in_service(tmp_path: Path) -> None:
    """DefaultArchLinterService detects circular imports in AST dependency graphs."""
    (tmp_path / "a.py").write_text("import b\n")
    (tmp_path / "b.py").write_text("import a\n")

    svc = DefaultArchLinterService()
    res = svc.detect_circular_imports(str(tmp_path))
    assert isinstance(res, CircularImportResult)
    assert res.status == "ok"
    assert res.has_circular_imports is True
    assert res.cycles_count >= 1


@pytest.mark.unit
def test_module_coupling_metrics(tmp_path: Path) -> None:
    """DefaultArchLinterService calculates Ca, Ce, and Instability metrics."""
    (tmp_path / "core.py").write_text("def run(): pass\n")
    (tmp_path / "client.py").write_text("import core\n")

    svc = DefaultArchLinterService()
    res = svc.compute_module_coupling(str(tmp_path))
    assert isinstance(res, ModuleCouplingResult)
    assert res.status == "ok"
    metrics = {m["module"]: m for m in res.metrics}
    assert "core" in metrics
    assert "client" in metrics
    assert metrics["core"]["afferent_coupling_Ca"] == 1
    assert metrics["client"]["efferent_coupling_Ce"] == 1


@pytest.mark.unit
def test_boundary_violation_detection(tmp_path: Path) -> None:
    """DefaultArchLinterService verifies inward architectural layer hierarchy."""
    (tmp_path / "kernel.py").write_text("import ui\n")
    (tmp_path / "ui.py").write_text("pass\n")

    svc = DefaultArchLinterService()
    res = svc.verify_clean_boundaries(str(tmp_path), layer_hierarchy=["kernel", "ui"])
    assert isinstance(res, BoundaryCheckResult)
    assert res.status == "ok"
    assert res.clean is False
    assert res.violations_count == 1


@pytest.mark.unit
def test_resolve_arch_linter_without_context() -> None:
    """resolve_arch_linter falls back to DefaultArchLinterService when context is empty or None."""
    svc_none = resolve_arch_linter(None)
    assert isinstance(svc_none, DefaultArchLinterService)

    empty_ctx = ServiceContext()
    svc_empty = resolve_arch_linter(empty_ctx)
    assert isinstance(svc_empty, DefaultArchLinterService)


@pytest.mark.asyncio
async def test_resolve_arch_linter_with_registered_plugin() -> None:
    """resolve_arch_linter returns the registered plugin service from ServiceContext."""
    ctx = ServiceContext()
    plugin = ArchLinterPlugin()
    await plugin.on_load(ctx)

    svc = resolve_arch_linter(ctx)
    assert svc is plugin
    lint_res = svc.lint_file("test.py", content="answer = 42\n")
    assert isinstance(lint_res, FileLintResult)
    assert lint_res.is_clean is True


@pytest.mark.unit
def test_plugin_module_singleton_export() -> None:
    """Rule 45: Plugin entrypoint must export module-level singleton plugin instance."""
    assert arch_linter_singleton is not None
    assert isinstance(arch_linter_singleton, ArchLinterPlugin)
    assert arch_linter_singleton.name == "plugin.arch_linter"
