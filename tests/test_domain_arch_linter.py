"""Tests for Architecture Linter plugin."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services.arch_linter import (
    ARCH_LINTER_KEY,
    ArchLinterService,
    BoundaryCheckResult,
    CircularImportResult,
    ModuleCouplingResult,
)
from plugins.software_engineering.arch_linter.main import (
    ArchLinterPlugin,
    compute_module_coupling,
    detect_circular_imports,
    verify_clean_boundaries,
)


@pytest.mark.unit
class TestArchLinterPlugin:
    def test_detect_circular_imports(self, tmp_path: Path) -> None:
        # Create cyclic modules: a -> b -> a
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")

        res = detect_circular_imports(str(tmp_path))
        assert res["status"] == "ok"
        assert res["has_circular_imports"] is True
        assert res["cycles_count"] >= 1

    def test_compute_module_coupling(self, tmp_path: Path) -> None:
        (tmp_path / "core.py").write_text("def run(): pass\n")
        (tmp_path / "client.py").write_text("import core\n")

        res = compute_module_coupling(str(tmp_path))
        assert res["status"] == "ok"
        metrics = {m["module"]: m for m in res["metrics"]}
        assert metrics["core"]["afferent_coupling_Ca"] == 1
        assert metrics["client"]["efferent_coupling_Ce"] == 1

    def test_verify_clean_boundaries(self, tmp_path: Path) -> None:
        (tmp_path / "kernel.py").write_text("import ui\n")
        (tmp_path / "ui.py").write_text("pass\n")

        res = verify_clean_boundaries(str(tmp_path), layer_hierarchy=["kernel", "ui"])
        assert res["status"] == "ok"
        assert res["clean"] is False
        assert res["violations_count"] == 1

    @pytest.mark.asyncio
    async def test_arch_linter_plugin_ioc_lifecycle(self, tmp_path: Path) -> None:
        plugin = ArchLinterPlugin()
        assert plugin.name == "plugin.arch_linter"
        assert ARCH_LINTER_KEY in plugin.provides

        ctx = ServiceContext()
        await plugin.on_load(ctx)
        await plugin.on_enable()

        service = ctx.require(ARCH_LINTER_KEY)
        assert isinstance(service, ArchLinterService)

        (tmp_path / "mod_a.py").write_text("def foo(): pass\n")
        (tmp_path / "mod_b.py").write_text("import mod_a\n")

        circ_res = service.detect_circular_imports(str(tmp_path))
        assert isinstance(circ_res, CircularImportResult)
        assert circ_res.status == "ok"
        assert circ_res.has_circular_imports is False

        coup_res = service.compute_module_coupling(str(tmp_path))
        assert isinstance(coup_res, ModuleCouplingResult)
        assert coup_res.status == "ok"
        assert coup_res.total_modules == 2

        bound_res = service.verify_clean_boundaries(str(tmp_path), layer_hierarchy=["mod_a", "mod_b"])
        assert isinstance(bound_res, BoundaryCheckResult)
        assert bound_res.status == "ok"
        assert bound_res.clean is True

        await plugin.on_disable()
        await plugin.on_unload()
