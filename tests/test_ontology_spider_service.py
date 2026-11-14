"""Contract tests for micro-kernel OntologySpiderKernelService, live vault ingestion, and skill/plugin validators."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from harness.creator.skills.validator import SkillValidator
from harness.creator.validator.engine import PluginValidator
from harness.services import (
    ONTOLOGY_SPIDER_SERVICE_KEY,
    AttributeEntropyRank,
    CompetencyScorecardReport,
    EpistemicVaultAuditReport,
    OntologySpiderKernelService,
    OntologySpiderProtocol,
)
from plugins.memory_and_epistemics.ontology_spider.adapter import HAS_ONTOLOGY_SPIDER

skip_if_no_engine = pytest.mark.skipif(
    not HAS_ONTOLOGY_SPIDER,
    reason="Ontology-Spider engine is not installed",
)


def test_frozen_dataclasses_immutability_and_validation() -> None:
    """Verify Rule 12 & Rule 43 frozen dataclass guards on value objects and reports."""
    rank = AttributeEntropyRank(
        attribute="category",
        entropy_bits=1.25,
        coverage=0.9,
        distinct_values=3,
        laya_score=1.125,
    )
    with pytest.raises((AttributeError, TypeError)):
        rank.laya_score = 0.0  # type: ignore[misc]

    with pytest.raises(ValueError):
        AttributeEntropyRank(attribute="bad", entropy_bits=-1.0, coverage=0.5, distinct_values=1, laya_score=0.0)

    report = CompetencyScorecardReport(
        vault_uri="urn:vault:test",
        total_questions=1,
        answered_questions=1,
        violation_count=0,
        clarity=1.0,
        coherence=1.0,
        extendibility=0.5,
        minimal_encoding_bias=1.0,
        minimal_commitment=1.0,
        overall_score=0.9,
        question_results=({"query": "query what is x?", "passed": True, "answers_count": 1},),
    )
    with pytest.raises((AttributeError, TypeError)):
        report.overall_score = 0.1  # type: ignore[misc]

    audit = EpistemicVaultAuditReport(
        vault_uri="urn:vault:test",
        entities_count=2,
        assertions_count=1,
        structural_violations=(),
        unverified_entity_ids=("ki_unverified",),
        top_discriminating_attributes=(rank,),
        gruber_coherence=1.0,
        status="verified",
    )
    with pytest.raises((AttributeError, TypeError)):
        audit.status = "violations_detected"  # type: ignore[misc]


@skip_if_no_engine
def test_kernel_service_phase5_queries_entropy_competency_and_audit() -> None:
    """Verify Phase-5 path/not/count queries, hop-distance ranking, entropy ranking, and epistemic audits."""
    service = OntologySpiderKernelService()
    assert isinstance(service, OntologySpiderProtocol)
    assert ONTOLOGY_SPIDER_SERVICE_KEY.name == "memory.ontology_spider_service"

    vault = {
        "vault_id": "phase5_test",
        "items": [
            {"id": "svc_api", "type": "service", "metadata": {"tier": "edge", "lang": "py", "isnad_verified": True}},
            {"id": "svc_core", "type": "service", "metadata": {"tier": "core", "lang": "py", "isnad_verified": True}},
            {
                "id": "db_store",
                "type": "database",
                "metadata": {"tier": "data", "lang": "sql", "isnad_verified": False},
            },
        ],
        "edges": [
            {"from": "service", "rel": "subclass_of", "to": "component"},
            {"from": "database", "rel": "subclass_of", "to": "component"},
            {"from": "depends_on", "rel": "domain", "to": "component"},
            {"from": "depends_on", "rel": "range", "to": "component"},
            {"from": "svc_api", "rel": "depends_on", "to": "svc_core"},
            {"from": "svc_core", "rel": "depends_on", "to": "db_store"},
        ],
    }

    path_res = service.query(vault, "query path via depends_on from svc_api to db_store")
    assert path_res["answers"][0]["value"] == "svc_api -> svc_core -> db_store"

    neg_res = service.query(vault, "query not db_store depends_on svc_api")
    assert neg_res["answers"][0]["value"] == "true"

    count_res = service.query(vault, "query count transitive depends_on from svc_api")
    assert count_res["answers"][0]["value"] == 2

    ranked_res = service.query(vault, "query transitive depends_on from svc_api", rank_by_distance=True)
    assert ranked_res["answers"][0]["value"] == "svc_core"
    assert ranked_res["answers"][0]["hop_distance"] == 1
    assert ranked_res["answers"][1]["hop_distance"] == 2
    assert ranked_res["answers"][0]["distance_score"] > ranked_res["answers"][1]["distance_score"]

    attrs = service.rank_attributes(vault, ["svc_api", "svc_core", "db_store"])
    assert len(attrs) >= 2
    assert attrs[0].attribute == "tier"

    scorecard = service.evaluate_competency(
        vault,
        ["query path via depends_on from svc_api to db_store", "query count transitive depends_on from svc_api"],
    )
    assert scorecard.answered_questions == 2
    assert scorecard.coherence == 1.0

    audit = service.audit_vault_epistemics(vault)
    assert audit.status == "verified"
    assert audit.unverified_entity_ids == ("db_store",)


@skip_if_no_engine
def test_live_harness_knowledge_vault_ingestion_and_runner() -> None:
    """Verify live .harness/knowledge/ canonical directory ingestion and headless runner CLI."""
    vault_dir = Path(".harness/knowledge")
    if not vault_dir.exists():
        pytest.skip(".harness/knowledge directory missing")

    service = OntologySpiderKernelService()
    audit = service.audit_vault_epistemics(vault_dir)
    assert audit.entities_count > 100
    assert audit.assertions_count > 100
    assert isinstance(audit.top_discriminating_attributes, tuple)

    runner_path = Path(".agents/skills/ontology-spider/scripts/ontology_spider_runner.py")
    proc = subprocess.run(
        [
            sys.executable,
            str(runner_path),
            "--vault",
            str(vault_dir),
            "--query",
            "query count ki_5d_complexity_baseline references_code ?",
            "--rank-entropy",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    parsed = json.loads(proc.stdout)
    assert parsed["query"]["answers"][0]["value"] >= 1
    assert len(parsed["entropy_ranks"]) >= 1


def test_skill_and_plugin_validators_pass() -> None:
    """Verify Rule 34, Rule 37, Rule 38, and Rule 44 craft and plugin validator gates."""
    skill_report = SkillValidator.validate_sync(Path(".agents/skills/ontology-spider"))
    failing_skill_checks = [c.message for c in skill_report.checks if not c.passed]
    assert skill_report.valid, f"Skill validation failed: {failing_skill_checks}"

    plugin_report = PluginValidator.validate_sync(
        Path("plugins/memory_and_epistemics/ontology_spider"),
        dry_run=True,
    )
    failing_plugin_checks = [c.message for c in plugin_report.checks if not c.passed]
    assert plugin_report.valid, f"Plugin validation failed: {failing_plugin_checks}"
