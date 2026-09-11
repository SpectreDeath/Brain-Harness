"""Tests for Google Style Guide Auditor Plugin."""

import pytest
from pathlib import Path
from harness.kernel.context import ServiceContext
from plugins.software_engineering.google_styleguide_auditor.main import (
    GOOGLE_STYLEGUIDE_AUDITOR_SERVICE_KEY,
    GoogleStyleguideAuditorPlugin,
)

@pytest.mark.asyncio
async def test_google_styleguide_auditor_tools(tmp_path: Path):
    ctx = ServiceContext()
    p = GoogleStyleguideAuditorPlugin()
    await p.enable(ctx)

    service = ctx.require(GOOGLE_STYLEGUIDE_AUDITOR_SERVICE_KEY)
    assert service is not None

    # Test audit_file with a clean python file
    clean_file = tmp_path / "clean.py"
    clean_file.write_text("def add(x: int, y: int) -> int:\n    return x + y\n", encoding="utf-8")
    audit_res = service.audit_file(str(clean_file), "python")
    assert audit_res["status"] == "success"
    assert audit_res["compliant"] is True

    # Test audit_file with style violations (wildcard import & mutable default)
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("from math import *\ndef bad(items=[]):\n    pass\n", encoding="utf-8")
    bad_audit = service.audit_file(str(bad_file), "python")
    assert bad_audit["compliant"] is False
    assert len(bad_audit["violations"]) >= 2

    # Test get_rule
    rule = service.get_rule("python", "imports")
    assert rule["status"] == "success"
    assert "import" in rule["guideline"].lower()

    # Test generate_linter_config
    cfg = service.generate_linter_config("pylint")
    assert cfg["status"] == "success"
    assert len(cfg["config_preview"]) > 0

    await p.disable(ctx)
