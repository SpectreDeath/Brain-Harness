"""Contract tests for the shim-harness-governor deep skill."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

_SKILL_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _SKILL_DIR.parents[2]
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
if str(_SKILL_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR / "scripts"))

from harness.creator.skills import SkillValidator  # noqa: E402
from harness.kernel.context import ServiceContext  # noqa: E402
from harness.services.shim_harness_governor import (  # noqa: E402
    SHIM_HARNESS_GOVERNOR_KEY,
    ShimHarnessGovernorEngine,
    ShimHarnessGovernorProtocol,
)
import shim_governor_engine  # noqa: E402


@pytest.mark.asyncio
async def test_shim_skill_validates_cleanly() -> None:
    report = await SkillValidator.validate_async(_SKILL_DIR)
    assert report.valid, [f"{c.rule}: {c.message}" for c in report.checks if not c.passed]


def test_shim_skill_exports_service_and_cli_wrapper(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ctx = ServiceContext()
    engine = ShimHarnessGovernorEngine()
    ctx.provide(SHIM_HARNESS_GOVERNOR_KEY, engine, provider="test")
    resolved = ctx.require(SHIM_HARNESS_GOVERNOR_KEY)
    assert isinstance(resolved, ShimHarnessGovernorProtocol)

    rc = shim_governor_engine.main(
        ["audit-tool", "--mode", "read-only", "--level", "read", "--root", str(tmp_path), "--target", "note.txt"]
    )
    assert rc == 0
    captured = capsys.readouterr().out
    assert '"allowed": true' in captured
