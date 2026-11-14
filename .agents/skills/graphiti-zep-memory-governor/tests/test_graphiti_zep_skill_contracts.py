"""Skill-local contract tests for graphiti-zep-memory-governor (Rule 57 unique basename)."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SRC_ROOT = _REPO_ROOT / "src"
for _candidate in (str(_SRC_ROOT), str(_REPO_ROOT)):
    if _candidate not in sys.path:
        sys.path.insert(0, _candidate)

from harness.creator.skills import SkillValidator  # noqa: E402
from harness.services.graphiti_zep_memory import (  # noqa: E402
    DEFAULT_RRF_RANK_CONST,
    FUZZY_JACCARD_THRESHOLD,
    MINHASH_BAND_SIZE,
    MINHASH_PERMUTATIONS,
    NAME_ENTROPY_THRESHOLD,
    GraphitiZepMemoryEngine,
)

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "graphiti_zep_memory_engine.py"


@pytest.mark.asyncio
async def test_skill_directory_passes_skill_validator() -> None:
    report = await SkillValidator.validate_async(SKILL_DIR)
    assert report.valid, f"Skill validation failed: {report.errors}"
    assert NAME_ENTROPY_THRESHOLD == 1.5
    assert FUZZY_JACCARD_THRESHOLD == 0.9
    assert MINHASH_PERMUTATIONS == 32
    assert MINHASH_BAND_SIZE == 4
    assert DEFAULT_RRF_RANK_CONST == 1


def test_skill_cli_smoke_subcommand() -> None:
    res = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "normalize-temporal",
            "--fact",
            "Alice plans to ship the service by Friday",
            "--reference-time",
            "2026-11-01T12:00:00Z",
            "--valid-at",
            "2026-11-06T12:00:00Z",
            "--invalid-at",
            "2026-11-06T23:59:00Z",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert res.returncode == 0, res.stderr
    payload = json.loads(res.stdout)
    assert payload["future_assertion_detected"] is True
    assert payload["soft_deadline_cleared"] is True
    assert payload["normalized_valid_at"] == "2026-11-01T12:00:00+00:00"
    assert payload["normalized_invalid_at"] is None


def test_engine_frozen_immutability_contract() -> None:
    engine = GraphitiZepMemoryEngine()
    rep = engine.rerank_hybrid_results(method="rrf", ranked_lists=[["u1", "u2"], ["u2", "u3"]])
    assert rep.ranked_uuids[0] == "u2"
    with pytest.raises((AttributeError, TypeError)):
        rep.method = "mmr"  # type: ignore[misc]
