"""Tests for Domain 4: Architecture Linter plugin."""

from __future__ import annotations

from pathlib import Path

import pytest

from plugins.arch_linter.main import (
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
