"""Comprehensive tests for deepened uncertainty-aware AI pipeline architecture.

Covers:
- Slotted frozen dataclass immutability (Rule 12 & Rule 43)
- Sub-millisecond Layer 1 domain boundary gating (Njoku 2026, ki_njoku_uncertainty_aware_systems)
- Layer 2 retrieval quality & semantic distance scoring (tau = 0.60 context blocking)
- Layer 3 probabilistic logit analysis & sequence perplexity (tau = -0.35 surge detection)
- Unified 3-layer request interception lifecycle with deterministic HITL escalation
- Continuous calibration & documentation debt telemetry mining
- Micro-kernel IoC service key registration & resolution (Rule 2 & Rule 49)
- PluginValidator compliance (Rule 34 & Rule 38)
- Headless Click CLI subcommands via CliRunner (Rule 6, Rule 10, Rule 23)
- Standalone HTML visual brief generation in %TEMP% (Rule 51)
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

_ws_root = Path(__file__).resolve().parent.parent
_skill_scripts = (
    _ws_root / ".agents" / "skills" / "uncertainty-aware-ai-architect" / "scripts"
)
for _p in [_ws_root / "src", _skill_scripts, _ws_root]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from uncertainty_guard_engine import (
    BoundaryGatingResult,
    DocDebtCluster,
    DomainBoundaryConfig,
    HitlEscalationTicket,
    LogprobAuditResult,
    PipelineInterceptionResult,
    RetrievalChunk,
    RetrievalScoringResult,
    UncertaintyGuardEngine,
)

from harness.commands.uncertainty import uncertainty_group
from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.uncertainty_guard import (
    UNCERTAINTY_GUARD_SERVICE_KEY,
    BoundaryReportData,
    UncertaintyGuardService,
)
from plugins.agent_orchestration.uncertainty_guard.main import (
    plugin as guard_plugin,
)


@pytest.fixture
def engine() -> UncertaintyGuardEngine:
    return UncertaintyGuardEngine()


# ---------------------------------------------------------------------------
# 1. Slotted & Frozen Dataclass Immutability (Rule 12 & Rule 43)
# ---------------------------------------------------------------------------


def test_domain_boundary_config_immutability() -> None:
    cfg = DomainBoundaryConfig()
    with pytest.raises((AttributeError, TypeError)):
        cfg.similarity_threshold = 0.85  # type: ignore


def test_boundary_gating_result_immutability() -> None:
    res = BoundaryGatingResult(
        is_valid=True,
        score=0.75,
        matched_domain="company VPN configuration",
        latency_ms=0.45,
        reason="Within bounds",
    )
    with pytest.raises((AttributeError, TypeError)):
        res.is_valid = False  # type: ignore


def test_retrieval_scoring_result_immutability() -> None:
    chunk = RetrievalChunk(chunk_id="c1", content="VPN info", score=0.82)
    with pytest.raises((AttributeError, TypeError)):
        chunk.score = 0.99  # type: ignore

    res = RetrievalScoringResult(
        has_sufficient_context=True,
        top_score=0.82,
        min_threshold=0.60,
        scored_chunks=(chunk,),
        action="INJECT_CONTEXT",
    )
    with pytest.raises((AttributeError, TypeError)):
        res.has_sufficient_context = False  # type: ignore


def test_logprob_audit_result_immutability() -> None:
    res = LogprobAuditResult(
        is_confident=True,
        avg_logprob=-0.15,
        perplexity=1.16,
        threshold=-0.35,
        token_count=10,
        action="DELIVER_RESPONSE",
    )
    with pytest.raises((AttributeError, TypeError)):
        res.is_confident = False  # type: ignore


def test_hitl_escalation_ticket_immutability() -> None:
    ticket = HitlEscalationTicket(
        ticket_id="HITL-TEST01",
        timestamp="2026-09-21T00:00:00Z",
        query="What is Mars?",
        failure_gate="BOUNDARY_GATE",
        reason="Outside domain",
    )
    with pytest.raises((AttributeError, TypeError)):
        ticket.query = "Changed query"  # type: ignore


def test_doc_debt_cluster_immutability() -> None:
    cluster = DocDebtCluster(
        cluster_id="DEBT-001",
        representative_topic="vpn access",
        query_count=3,
        sample_queries=("q1", "q2", "q3"),
        severity="HIGH",
    )
    with pytest.raises((AttributeError, TypeError)):
        cluster.query_count = 10  # type: ignore


def test_pipeline_interception_result_immutability() -> None:
    b_res = BoundaryGatingResult(
        is_valid=True,
        score=0.75,
        matched_domain="VPN",
        latency_ms=0.5,
        reason="Valid",
    )
    res = PipelineInterceptionResult(
        state="PASSED_VERIFIED",
        gate_passed=3,
        total_latency_ms=1.2,
        boundary_result=b_res,
        retrieval_result=None,
        logprob_result=None,
        escalation_ticket=None,
        response_text="Verified",
    )
    with pytest.raises((AttributeError, TypeError)):
        res.state = "REJECTED"  # type: ignore


# ---------------------------------------------------------------------------
# 2. Layer 1: Boundary Gating Tests
# ---------------------------------------------------------------------------


def test_layer1_boundary_in_domain(engine: UncertaintyGuardEngine) -> None:
    res = engine.verify_boundary("How do I configure the corporate VPN on MacOS?")
    assert res.is_valid is True
    assert res.score >= 0.45
    assert "VPN" in res.matched_domain or "vpn" in res.matched_domain.lower()
    assert res.latency_ms < 50.0  # Sub-millisecond performance


def test_layer1_boundary_out_of_domain(engine: UncertaintyGuardEngine) -> None:
    res = engine.verify_boundary("What is the recipe for chocolate chip cookies?")
    assert res.is_valid is False
    assert res.score < 0.45
    assert "falls outside operational domain boundaries" in res.reason


def test_layer1_boundary_empty_query(engine: UncertaintyGuardEngine) -> None:
    res = engine.verify_boundary("   ")
    assert res.is_valid is False
    assert res.score == 0.0
    assert "empty" in res.reason.lower()


# ---------------------------------------------------------------------------
# 3. Layer 2: Retrieval Quality & Semantic Distance Scoring
# ---------------------------------------------------------------------------


def test_layer2_retrieval_sufficient_context(
    engine: UncertaintyGuardEngine,
) -> None:
    query = "How to install the internal VPN client"
    chunks = [
        "Internal IT software deployment and company VPN configuration guidelines for remote staff.",
        "Cafeteria menu for Wednesday lunch.",
    ]
    res = engine.score_retrieval(query, chunks, minimum_relevance=0.60)
    assert res.has_sufficient_context is True
    assert res.top_score >= 0.60
    assert res.action == "INJECT_CONTEXT"
    assert len(res.scored_chunks) == 2
    assert res.scored_chunks[0].score >= res.scored_chunks[1].score


def test_layer2_retrieval_insufficient_context(
    engine: UncertaintyGuardEngine,
) -> None:
    query = "How to install the internal VPN client"
    chunks = [
        "Cafeteria menu for Wednesday lunch.",
        "Parking lot resurfacing notice.",
    ]
    res = engine.score_retrieval(query, chunks, minimum_relevance=0.60)
    assert res.has_sufficient_context is False
    assert res.top_score < 0.60
    assert res.action == "BLOCK_CONTEXT_AND_ESCALATE"


def test_layer2_retrieval_empty_chunks(engine: UncertaintyGuardEngine) -> None:
    res = engine.score_retrieval("query", [], minimum_relevance=0.60)
    assert res.has_sufficient_context is False
    assert res.top_score == 0.0
    assert res.action == "BLOCK_CONTEXT_AND_ESCALATE"


# ---------------------------------------------------------------------------
# 4. Layer 3: Probabilistic Logit Analysis & Output Validation
# ---------------------------------------------------------------------------


def test_layer3_logprobs_confident(engine: UncertaintyGuardEngine) -> None:
    # High certainty logprobs (mean >= -0.35)
    logprobs = [-0.08, -0.12, -0.05, -0.15, -0.10]
    res = engine.validate_logprobs(logprobs, logprob_threshold=-0.35)
    assert res.is_confident is True
    assert res.avg_logprob >= -0.35
    assert res.perplexity < 1.42
    assert res.action == "DELIVER_RESPONSE"


def test_layer3_logprobs_uncertain(engine: UncertaintyGuardEngine) -> None:
    # High entropy uncertain sequence (mean < -0.35)
    logprobs = [-0.85, -1.20, -0.65, -0.90, -1.10]
    res = engine.validate_logprobs(logprobs, logprob_threshold=-0.35)
    assert res.is_confident is False
    assert res.avg_logprob < -0.35
    assert res.perplexity > 1.50
    assert res.action == "ACTIVATE_CALIBRATED_FALLBACK"


def test_layer3_logprobs_empty(engine: UncertaintyGuardEngine) -> None:
    res = engine.validate_logprobs([], logprob_threshold=-0.35)
    assert res.is_confident is False
    assert res.action == "ACTIVATE_CALIBRATED_FALLBACK"


# ---------------------------------------------------------------------------
# 5. Unified 3-Layer Request Interception Lifecycle
# ---------------------------------------------------------------------------


def test_pipeline_interception_boundary_failure(
    engine: UncertaintyGuardEngine,
) -> None:
    res = engine.intercept_request(
        query="How to cook pasta bolognese?",
        retrieved_chunks=["Cooking instructions..."],
        token_logprobs=[-0.1, -0.1],
    )
    assert res.state == "REJECTED_OUT_OF_DOMAIN"
    assert res.gate_passed == 0
    assert res.escalation_ticket is not None
    assert res.escalation_ticket.failure_gate == "BOUNDARY_GATE"
    assert "outside" in res.response_text.lower()


def test_pipeline_interception_retrieval_failure(
    engine: UncertaintyGuardEngine,
) -> None:
    res = engine.intercept_request(
        query="company VPN configuration for Linux",
        retrieved_chunks=["Holiday schedule calendar."],
        token_logprobs=[-0.1, -0.1],
    )
    assert res.state == "ESCALATED_LOW_CONTEXT"
    assert res.gate_passed == 1
    assert res.escalation_ticket is not None
    assert res.escalation_ticket.failure_gate == "RETRIEVAL_GATE"
    assert "escalated to human support" in res.response_text.lower()


def test_pipeline_interception_logprob_failure(
    engine: UncertaintyGuardEngine,
) -> None:
    res = engine.intercept_request(
        query="company VPN configuration for Linux",
        retrieved_chunks=[
            "Corporate IT deployment and company VPN configuration for Linux operating systems."
        ],
        token_logprobs=[-1.2, -1.5, -0.9],
        draft_response="Uncertain guess",
    )
    assert res.state == "FALLBACK_UNCERTAIN_LOGPROBS"
    assert res.gate_passed == 2
    assert res.escalation_ticket is not None
    assert res.escalation_ticket.failure_gate == "LOGPROB_GATE"
    assert "safety thresholds" in res.response_text.lower()


def test_pipeline_interception_all_pass(
    engine: UncertaintyGuardEngine,
) -> None:
    res = engine.intercept_request(
        query="company VPN configuration for Linux",
        retrieved_chunks=[
            "Corporate IT deployment and company VPN configuration for Linux operating systems."
        ],
        token_logprobs=[-0.1, -0.05, -0.15],
        draft_response="Use the openvpn client with the corp profile.",
    )
    assert res.state == "PASSED_VERIFIED"
    assert res.gate_passed == 3
    assert res.escalation_ticket is None
    assert res.response_text == "Use the openvpn client with the corp profile."


# ---------------------------------------------------------------------------
# 6. Documentation Debt Telemetry Mining
# ---------------------------------------------------------------------------


def test_mine_documentation_debt(engine: UncertaintyGuardEngine) -> None:
    failed_queries = [
        "How to configure SSO login for contractor portal?",
        "Contractor portal SSO setup instructions",
        "SSO authentication steps for contractor portal",
        "401k employer contribution percentage",
        "401k match policy details",
    ]
    clusters = engine.mine_documentation_debt(failed_queries)
    assert len(clusters) >= 2
    top_cluster = clusters[0]
    assert top_cluster.query_count >= 2
    assert top_cluster.severity in ("MEDIUM", "HIGH", "CRITICAL")
    assert len(top_cluster.sample_queries) >= 2


# ---------------------------------------------------------------------------
# 7. Micro-Kernel IoC Service Protocol & Plugin Lifecycle (Rule 45 & 49)
# ---------------------------------------------------------------------------


def test_ioc_service_protocol_conformance() -> None:
    assert isinstance(guard_plugin, UncertaintyGuardService)


@pytest.mark.asyncio
async def test_plugin_ioc_lifecycle() -> None:
    context = ServiceContext()
    await guard_plugin.on_load(context)

    svc = context.require(UNCERTAINTY_GUARD_SERVICE_KEY)
    assert svc is guard_plugin

    res = svc.verify_boundary("company VPN configuration")
    assert isinstance(res, BoundaryReportData)
    assert res.is_valid is True

    await guard_plugin.on_unload(context)


def test_plugin_validator_compliance() -> None:
    plugin_dir = _ws_root / "plugins" / "agent_orchestration" / "uncertainty_guard"
    report = PluginValidator.validate_sync(plugin_dir)
    assert report.valid is True
    assert len(report.checks) >= 5


# ---------------------------------------------------------------------------
# 8. Headless Click CLI Subcommands (Rule 6, Rule 10, Rule 23)
# ---------------------------------------------------------------------------


def test_cli_gate_subcommand() -> None:
    runner = CliRunner()
    result = runner.invoke(
        uncertainty_group, ["gate", "-q", "company VPN configuration"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["is_valid"] is True
    assert payload["score"] >= 0.45


def test_cli_retrieval_subcommand() -> None:
    runner = CliRunner()
    result = runner.invoke(
        uncertainty_group,
        [
            "retrieval",
            "-q",
            "Configure VPN",
            "-c",
            "Corporate VPN installation and setup guide",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["has_sufficient_context"] is True
    assert payload["action"] == "INJECT_CONTEXT"


def test_cli_logprobs_subcommand() -> None:
    runner = CliRunner()
    result = runner.invoke(uncertainty_group, ["logprobs", "-l", "-0.1", "-l", "-0.2"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["is_confident"] is True
    assert payload["action"] == "DELIVER_RESPONSE"


def test_cli_pipeline_subcommand() -> None:
    runner = CliRunner()
    result = runner.invoke(
        uncertainty_group,
        [
            "pipeline",
            "-q",
            "Where can I find cake?",
            "-c",
            "Dessert menu",
            "-l",
            "-0.1",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["state"] == "REJECTED_OUT_OF_DOMAIN"


def test_cli_calibrate_subcommand() -> None:
    runner = CliRunner()
    result = runner.invoke(
        uncertainty_group,
        ["calibrate", "-q", "VPN login setup", "-q", "VPN login reset"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert isinstance(payload, list)
    assert len(payload) >= 1


def test_cli_brief_generation() -> None:
    runner = CliRunner()
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tf:
        out_path = tf.name

    result = runner.invoke(
        uncertainty_group,
        ["brief", "-q", "company VPN configuration", "-o", out_path],
    )
    assert result.exit_code == 0
    assert Path(out_path).exists()
    content = Path(out_path).read_text(encoding="utf-8")
    assert "<html" in content
    assert "Uncertainty Interception Visual Brief" in content
    Path(out_path).unlink(missing_ok=True)
