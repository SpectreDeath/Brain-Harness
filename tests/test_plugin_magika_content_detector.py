"""Tests for Google Magika Content Detector Plugin."""

from __future__ import annotations

import base64
from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.creator.validator import PluginValidator
from plugins.security_and_forensics.magika_content_detector.main import (
    MAGIKA_CONTENT_DETECTOR_KEY,
    MagikaContentDetectorPlugin,
    MagikaContentDetectorService,
    magika_batch_scan,
    magika_get_model_info,
    magika_identify_bytes,
    magika_identify_path,
    magika_list_content_types,
)


@pytest.fixture
def plugin_dir() -> Path:
    target = Path(__file__).parent.parent / "plugins" / "security_and_forensics" / "magika_content_detector"
    assert target.exists(), f"Plugin directory missing: {target}"
    return target


@pytest.mark.unit
class TestMagikaContentDetectorPlugin:
    """Unit and lifecycle test suite for Google Magika content detection."""

    @pytest.mark.asyncio
    async def test_plugin_ioc_lifecycle(self) -> None:
        """Verify plugin registers typed ServiceKey into ServiceContext."""
        ctx = ServiceContext()
        plugin = MagikaContentDetectorPlugin()

        assert plugin.name == "plugin.magika_content_detector"
        assert MAGIKA_CONTENT_DETECTOR_KEY in plugin.provides

        await plugin.on_load(ctx)
        svc = ctx.require(MAGIKA_CONTENT_DETECTOR_KEY)
        assert isinstance(svc, MagikaContentDetectorService)

        await plugin.on_enable()
        await plugin.on_disable()
        await plugin.on_unload()

    def test_identify_path_python_file(self, tmp_path: Path) -> None:
        """Verify deep learning classification identifies Python file correctly."""
        py_file = tmp_path / "script.py"
        py_file.write_text("#!/usr/bin/env python3\nprint('hello world')\n", encoding="utf-8")

        res = magika_identify_path(str(py_file))
        assert res["status"] == "ok"
        assert res["label"] == "python"
        assert res["mime_type"] == "text/x-python"
        assert res["group"] == "code"
        assert res["is_text"] is True
        assert res["score"] > 0.5

    def test_identify_bytes_json(self) -> None:
        """Verify in-memory base64 byte classification without disk writes."""
        raw_json = b'{"status": "ok", "count": 42, "items": ["a", "b"]}'
        b64_str = base64.b64encode(raw_json).decode("ascii")

        res = magika_identify_bytes(b64_str)
        assert res["status"] == "ok"
        assert res["label"] in ("json", "jsonl")
        assert res["is_text"] is True
        assert res["score"] > 0.5

    def test_batch_scan_directory(self, tmp_path: Path) -> None:
        """Verify batch directory scanner catalogs group distributions."""
        (tmp_path / "app.py").write_text("import sys\nprint('running')\n", encoding="utf-8")
        (tmp_path / "config.json").write_text('{"host": "localhost"}', encoding="utf-8")
        (tmp_path / "notes.txt").write_text("Plain text documentation notes.\n", encoding="utf-8")

        scan = magika_batch_scan(str(tmp_path), recursive=True)
        assert scan["status"] == "ok"
        assert scan["scanned_count"] == 3
        assert "code" in scan["group_counts"]
        assert len(scan["files"]) == 3

    def test_list_content_types_and_model_info(self) -> None:
        """Verify knowledge base lookup and model metadata."""
        types_res = magika_list_content_types(filter_group="code")
        assert types_res["status"] == "ok"
        assert types_res["total_count"] > 0
        assert any(t["label"] == "python" for t in types_res["content_types"])

        model_info = magika_get_model_info()
        assert model_info["status"] == "ok"
        assert model_info["output_types_count"] >= 200
        assert "standard_v" in model_info["model_name"]

    @pytest.mark.asyncio
    async def test_plugin_validator_compliance(self, plugin_dir: Path) -> None:
        """Verify plugin passes 100% of PluginValidator pre-flight rules."""
        report = await PluginValidator.validate(plugin_dir, dry_run=False)
        assert report.valid is True, f"PluginValidator failed: {report.errors}"
