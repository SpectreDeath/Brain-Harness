"""Contract tests verifying Uncertainty CLI Commands decomposition.

Validates:
1. Strict submodule bounds (AGENTS.md Rule 11: all files <= 200 lines).
2. Click CLI Group single-source consolidation (AGENTS.md Rule 6).
3. Single-seam resolver conformance (AGENTS.md Rule 58).
4. Headless CLI introspection and command registration (AGENTS.md Rule 10).
5. Data model converter mappings.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
from click.testing import CliRunner
import pytest

from harness.commands.uncertainty import (
    UncertaintyEngineAdapter,
    _EngineAdapter,
    brief_cmd,
    calibrate_cmd,
    gate_cmd,
    get_uncertainty_service,
    logprobs_cmd,
    pipeline_cmd,
    resolve_uncertainty_service,
    retrieval_cmd,
    uncertainty_group,
)
from harness.kernel.context import ServiceContext
from harness.services.uncertainty_guard import (
    UNCERTAINTY_GUARD_SERVICE_KEY,
    BoundaryReportData,
    UncertaintyGuardService,
)


@pytest.mark.unit
class TestUncertaintyCommandsDecomposition:
    """Verify architectural invariants for uncertainty commands decomposition."""

    def test_submodule_line_count_bounds(self) -> None:
        """Rule 11: Verify every submodule in package is <= 200 lines."""
        pkg_dir = Path("src") / "harness" / "commands" / "uncertainty"
        py_files = list(pkg_dir.glob("*.py"))
        assert len(py_files) >= 10

        for py_file in py_files:
            lines = len(py_file.read_text(encoding="utf-8").splitlines())
            assert lines <= 200, f"{py_file.name} has {lines} lines, exceeding 200-line limit"

    def test_click_group_single_source_consolidation(self) -> None:
        """Rule 6: Verify uncertainty_group consolidates all required subcommands."""
        cmd_names = set(uncertainty_group.commands.keys())
        expected_cmds = {"gate", "retrieval", "logprobs", "pipeline", "calibrate", "brief"}
        assert expected_cmds.issubset(cmd_names)

        assert uncertainty_group.commands["gate"] is gate_cmd
        assert uncertainty_group.commands["retrieval"] is retrieval_cmd
        assert uncertainty_group.commands["logprobs"] is logprobs_cmd
        assert uncertainty_group.commands["pipeline"] is pipeline_cmd
        assert uncertainty_group.commands["calibrate"] is calibrate_cmd
        assert uncertainty_group.commands["brief"] is brief_cmd

    def test_resolver_single_seam(self) -> None:
        """Rule 58: Verify resolver behaves cleanly with and without ServiceContext."""
        # Resolution from ServiceContext when provided
        ctx = ServiceContext()
        mock_svc = MagicMock(spec=UncertaintyGuardService)
        ctx.provide(UNCERTAINTY_GUARD_SERVICE_KEY, mock_svc)

        resolved = get_uncertainty_service(ctx)
        assert resolved is mock_svc

        alias_resolved = resolve_uncertainty_service(ctx)
        assert alias_resolved is mock_svc

        # Fallback when context is None
        fallback_svc = get_uncertainty_service(None)
        assert isinstance(fallback_svc, UncertaintyGuardService)
        assert _EngineAdapter is UncertaintyEngineAdapter

    def test_cli_help_inspection(self) -> None:
        """Rule 10: Verify headless CLI help introspection on all subcommands."""
        runner = CliRunner()

        for cmd_name in ["gate", "retrieval", "logprobs", "pipeline", "calibrate", "brief"]:
            res = runner.invoke(uncertainty_group, [cmd_name, "--help"])
            assert res.exit_code == 0, f"Command {cmd_name} --help failed: {res.output}"
            assert "Usage:" in res.output

    def test_converters_contract(self) -> None:
        """Verify converters correctly transform raw data into slotted/dataclass models."""
        from harness.commands.uncertainty.converters import (
            to_boundary_report,
            to_doc_debt_clusters,
            to_escalation_ticket,
            to_logprob_report,
            to_retrieval_report,
        )

        # Boundary report
        raw_b = MagicMock(
            is_valid=True,
            score=0.92,
            matched_domain="test_domain",
            latency_ms=1.5,
            reason="Within threshold",
        )
        b_rep = to_boundary_report(raw_b)
        assert isinstance(b_rep, BoundaryReportData)
        assert b_rep.is_valid is True
        assert b_rep.score == 0.92

        # Escalation ticket none
        assert to_escalation_ticket(None) is None

        # Logprob report
        raw_lp = MagicMock(
            is_confident=True,
            avg_logprob=-0.1,
            perplexity=1.1,
            threshold=-0.35,
            token_count=5,
            action="allow",
        )
        lp_rep = to_logprob_report(raw_lp)
        assert lp_rep.is_confident is True
        assert lp_rep.avg_logprob == -0.1

        # Retrieval report
        chunk_mock = MagicMock(chunk_id="c1", content="text", score=0.85)
        raw_ret = MagicMock(
            has_sufficient_context=True,
            top_score=0.85,
            min_threshold=0.6,
            scored_chunks=[chunk_mock],
            action="allow",
        )
        ret_rep = to_retrieval_report(raw_ret)
        assert ret_rep.has_sufficient_context is True
        assert len(ret_rep.scored_chunks) == 1

        # Doc debt clusters
        cl_mock = MagicMock(
            cluster_id="cl1",
            representative_topic="VPN",
            query_count=3,
            sample_queries=["q1", "q2"],
            severity="high",
        )
        clusters = to_doc_debt_clusters([cl_mock])
        assert len(clusters) == 1
        assert clusters[0].cluster_id == "cl1"
