"""Tests for Google Magika Format Forensics Plugin."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.creator.validator import PluginValidator
from plugins.security_and_forensics.magika_content_detector.main import (
    MAGIKA_CONTENT_DETECTOR_KEY,
    MagikaContentDetectorPlugin,
)
from plugins.security_and_forensics.magika_format_forensics.main import (
    MAGIKA_FORMAT_FORENSICS_KEY,
    MagikaFormatForensicsPlugin,
    MagikaFormatForensicsService,
    magika_audit_extension_mismatch,
    magika_polyglot_check,
    magika_quarantine_scan,
)


@pytest.fixture
def plugin_dir() -> Path:
    target = Path(__file__).parent.parent / "plugins" / "security_and_forensics" / "magika_format_forensics"
    assert target.exists(), f"Plugin directory missing: {target}"
    return target


@pytest.mark.unit
class TestMagikaFormatForensicsPlugin:
    """Unit and lifecycle test suite for Magika format forensics and polyglot verification."""

    @pytest.mark.asyncio
    async def test_plugin_ioc_lifecycle(self) -> None:
        """Verify plugin registers typed ServiceKey and requires content detector."""
        ctx = ServiceContext()
        detector = MagikaContentDetectorPlugin()
        forensics = MagikaFormatForensicsPlugin()

        assert forensics.name == "plugin.magika_format_forensics"
        assert MAGIKA_FORMAT_FORENSICS_KEY in forensics.provides
        assert MAGIKA_CONTENT_DETECTOR_KEY in forensics.requires

        await detector.on_load(ctx)
        await forensics.on_load(ctx)

        svc = ctx.require(MAGIKA_FORMAT_FORENSICS_KEY)
        assert isinstance(svc, MagikaFormatForensicsService)

        await forensics.on_enable()
        await forensics.on_disable()
        await forensics.on_unload()

    def test_audit_extension_mismatch_critical(self, tmp_path: Path) -> None:
        """Verify extension spoofing detection flags executable disguised as image."""
        fake_png = tmp_path / "innocent.png"
        fake_png.write_text("#!/usr/bin/env python3\nimport os\nos.system('calc')\n", encoding="utf-8")

        audit = magika_audit_extension_mismatch(str(fake_png))
        assert audit["status"] == "ok"
        assert audit["mismatches_count"] == 1
        mismatch = audit["mismatches"][0]
        assert mismatch["file_extension"] == "png"
        assert mismatch["detected_label"] == "python"
        assert mismatch["risk_level"] == "critical"

    def test_audit_extension_mismatch_clean(self, tmp_path: Path) -> None:
        """Verify clean legitimate files produce zero false-positive mismatches."""
        clean_py = tmp_path / "clean.py"
        clean_py.write_text("#!/usr/bin/env python3\nimport sys\ndef main():\n    print('legitimate code')\nif __name__ == '__main__':\n    main()\n", encoding="utf-8")

        audit = magika_audit_extension_mismatch(str(clean_py))
        assert audit["status"] == "ok"
        assert audit["mismatches_count"] == 0

    def test_polyglot_check_appended_zip(self, tmp_path: Path) -> None:
        """Verify polyglot detector catches ZIP structures appended to non-ZIP headers."""
        polyglot_file = tmp_path / "sample.bin"
        header = b"\xFF\xD8\xFF\xE0" + b"\x00" * 1020
        zip_payload = b"PK\x03\x04" + b"\x00" * 1020
        polyglot_file.write_bytes(header + zip_payload)

        check = magika_polyglot_check(str(polyglot_file))
        assert check["status"] == "ok"
        assert check["is_polyglot_candidate"] is True
        assert any("ZIP" in ind for ind in check["indicators"])

    def test_quarantine_scan_blocked_group(self, tmp_path: Path) -> None:
        """Verify upload quarantine scan blocks prohibited content groups."""
        code_file = tmp_path / "payload.py"
        code_file.write_text("#!/usr/bin/env python3\nimport socket\n", encoding="utf-8")

        scan = magika_quarantine_scan(str(code_file), blocked_groups=["executable", "code"])
        assert scan["status"] == "ok"
        assert scan["quarantined"] is True
        assert "Prohibited content group 'code'" in scan["violation_reason"]

    def test_quarantine_scan_allowed(self, tmp_path: Path) -> None:
        """Verify upload quarantine scan permits permitted content groups."""
        doc_file = tmp_path / "readme.txt"
        doc_file.write_text("This is simple documentation.\n", encoding="utf-8")

        scan = magika_quarantine_scan(str(doc_file), blocked_groups=["executable"])
        assert scan["status"] == "ok"
        assert scan["quarantined"] is False

    @pytest.mark.asyncio
    async def test_plugin_validator_compliance(self, plugin_dir: Path) -> None:
        """Verify plugin passes 100% of PluginValidator pre-flight rules."""
        report = await PluginValidator.validate(plugin_dir, dry_run=False)
        assert report.valid is True, f"PluginValidator failed: {report.errors}"
