"""Skill-local contract tests for trustgraph-ontology-governor (Rule 57 unique basename)."""

from __future__ import annotations

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
from harness.services.trustgraph_governor import (  # noqa: E402
    DEFAULT_POLICY_ORDER,
    EXPLAINABILITY_STAGES,
    LAYA_HEAD_MAX_LEN,
    LAYA_MAX_SEQ_LEN,
    LAYA_TEMP_MAX,
    LAYA_TEMP_MIN,
    POLICY_GRAPH_URI,
    RETRIEVAL_GRAPH_URI,
    SOURCE_GRAPH_URI,
    TrustGraphGovernorEngine,
)

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "trustgraph_governor_engine.py"


@pytest.mark.asyncio
async def test_skill_directory_passes_skill_validator() -> None:
    report = await SkillValidator.validate_async(SKILL_DIR)
    assert report.valid, f"Skill validation failed: {report.errors}"
    assert POLICY_GRAPH_URI == "urn:graph:policy"
    assert DEFAULT_POLICY_ORDER == 99


def test_skill_cli_smoke_subcommands() -> None:
    res = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "score-decision",
            "--question-type",
            "choice",
            "--options-json",
            '["alpha", "beta", "gamma"]',
            "--logits-json",
            "[2.0, 0.5, 0.1]",
            "--temperature",
            "10.0",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert res.returncode == 0, res.stderr
    assert f'"clamped_temperature": {LAYA_TEMP_MAX}' in res.stdout
    assert f'"head_max_len": {LAYA_HEAD_MAX_LEN}' in res.stdout
    assert f'"max_seq_len": {LAYA_MAX_SEQ_LEN}' in res.stdout


def test_engine_core_invariants_quick_contract() -> None:
    engine = TrustGraphGovernorEngine()
    prov = engine.build_provenance_trace(
        question_id="q-42",
        query_text="Which gene regulates TP53?",
        document_id="doc-99",
        prompt_tokens=120,
        completion_tokens=45,
    )
    assert prov.source_graph == SOURCE_GRAPH_URI
    assert prov.retrieval_graph == RETRIEVAL_GRAPH_URI
    assert tuple(prov.stage_uris.keys()) == EXPLAINABILITY_STAGES
    assert prov.token_triples_appended is True
    assert prov.total_tokens == 165

    with pytest.raises((AttributeError, TypeError)):
        prov.question_id = "mutated"  # type: ignore[misc]
    assert LAYA_TEMP_MIN == 0.5
