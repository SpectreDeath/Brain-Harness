"""Comprehensive contract test suite for Differential Facet Verifier & Availability Semantics.

Validates:
1. Slotted/frozen dataclass immutability (Rule 12 & Rule 43)
2. __post_init__ construction invariants across domain models
3. Core differential facet semantics (absence claimability, facet conflation defense, 3-valued status)
4. Headless Click CLI introspection seams (Rule 10)
5. Ecosystem hygiene and Rule 40 dual-file Knowledge Item integrity
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.creator.skills import SkillValidator
from harness.services.differential_facet import (
    CoverageDeclaration,
    DifferentialReport,
    DimensionOutcome,
    FacetAvailability,
    StandardDifferentialFacetService,
    VALID_DIMENSIONS,
)
from harness.commands.facet import facet_group
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def ki_dir(repo_root: Path) -> Path:
    target = repo_root / ".harness" / "knowledge" / "ki-rea-facet-availability-semantics"
    assert target.exists(), f"Knowledge Item directory missing: {target}"
    return target


@pytest.fixture
def skill_dir(repo_root: Path) -> Path:
    target = repo_root / ".agents" / "skills" / "differential-facet-verifier"
    assert target.exists(), f"Skill directory missing: {target}"
    return target


# -----------------------------------------------------------------------------
# Block 1 — Slotted/Frozen Immutability (Rule 12 & Rule 43)
# -----------------------------------------------------------------------------

@pytest.mark.unit
class TestFacetAvailabilityImmutability:
    """Verify FacetAvailability slotted and frozen immutability."""

    def test_direct_mutation_raises(self) -> None:
        fa = FacetAvailability(available=True)
        with pytest.raises((AttributeError, TypeError)):
            fa.available = False  # type: ignore


@pytest.mark.unit
class TestCoverageDeclarationImmutability:
    """Verify CoverageDeclaration slotted and frozen immutability."""

    def test_direct_mutation_raises(self) -> None:
        cov = CoverageDeclaration(scope="dossier", status="complete")
        with pytest.raises((AttributeError, TypeError)):
            cov.status = "partial"  # type: ignore


@pytest.mark.unit
class TestDimensionOutcomeImmutability:
    """Verify DimensionOutcome slotted and frozen immutability."""

    def test_direct_mutation_raises(self) -> None:
        outcome = DimensionOutcome(
            dimension="assembly",
            status="unchanged",
            conclusion_kind="derived_relationship",
            left_digest="sha256:1111",
            right_digest="sha256:1111",
            left_count=10,
            right_count=10,
        )
        with pytest.raises((AttributeError, TypeError)):
            outcome.status = "changed"  # type: ignore


@pytest.mark.unit
class TestDifferentialReportImmutability:
    """Verify DifferentialReport slotted and frozen immutability."""

    def test_direct_mutation_raises(self) -> None:
        report = DifferentialReport(
            report_id="rep:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            overall_status="unchanged",
            left_evidence_id="ev:1111",
            right_evidence_id="ev:2222",
            dimensions=(),
            summary_digest="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        )
        with pytest.raises((AttributeError, TypeError)):
            report.overall_status = "changed"  # type: ignore


# -----------------------------------------------------------------------------
# Block 2 — __post_init__ Construction Invariants
# -----------------------------------------------------------------------------

@pytest.mark.unit
class TestFacetAvailabilityInvariants:
    """Verify FacetAvailability construction invariants."""

    def test_unavailable_without_reason_raises(self) -> None:
        with pytest.raises(ValueError, match="must declare a non-empty reason"):
            FacetAvailability(available=False, reason=None)

    def test_unavailable_with_whitespace_reason_raises(self) -> None:
        with pytest.raises(ValueError, match="must declare a non-empty reason"):
            FacetAvailability(available=False, reason="   ")


@pytest.mark.unit
class TestCoverageDeclarationInvariants:
    """Verify CoverageDeclaration construction invariants."""

    def test_invalid_status_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid coverage status"):
            CoverageDeclaration(scope="dossier", status="non_existent")


@pytest.mark.unit
class TestDimensionOutcomeInvariants:
    """Verify DimensionOutcome construction invariants."""

    def test_unknown_with_digests_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown dimension must not carry digests"):
            DimensionOutcome(
                dimension="pseudocode",
                status="unknown",
                conclusion_kind="unresolved",
                left_digest="sha256:abcd",
                right_digest=None,
                left_count=None,
                right_count=None,
            )

    def test_unknown_with_counts_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown dimension must carry null counts"):
            DimensionOutcome(
                dimension="pseudocode",
                status="unknown",
                conclusion_kind="unresolved",
                left_digest=None,
                right_digest=None,
                left_count=4,
                right_count=None,
            )


@pytest.mark.unit
class TestDifferentialReportInvariants:
    """Verify DifferentialReport construction invariants."""

    def test_report_id_prefix_enforced(self) -> None:
        with pytest.raises(ValueError, match="report_id must be prefixed rep:"):
            DifferentialReport(
                report_id="bad_prefix:1234",
                overall_status="unchanged",
                left_evidence_id="ev:1111",
                right_evidence_id="ev:2222",
                dimensions=(),
                summary_digest="1234",
            )

    def test_overall_unchanged_with_unknown_dim_raises(self) -> None:
        dim = DimensionOutcome(
            dimension="identity",
            status="unknown",
            conclusion_kind="unresolved",
            left_digest=None,
            right_digest=None,
            left_count=None,
            right_count=None,
        )
        with pytest.raises(ValueError, match="overall_status cannot be 'unchanged' when any dimension is 'unknown'"):
            DifferentialReport(
                report_id="rep:0000000000000000000000000000000000000000000000000000000000000000",
                overall_status="unchanged",
                left_evidence_id="ev:1111",
                right_evidence_id="ev:2222",
                dimensions=(dim,),
                summary_digest="0000000000000000000000000000000000000000000000000000000000000000",
            )


# -----------------------------------------------------------------------------
# Block 3 — Core Semantic Logic
# -----------------------------------------------------------------------------

@pytest.mark.unit
class TestAbsenceClaimability:
    """Verify formal absence claimability rule."""

    def test_complete_untruncated_zero_omitted_is_claimable(self) -> None:
        cov = CoverageDeclaration(scope="dossier", status="complete", truncated=False, omitted_count=0)
        assert cov.absence_claimable is True

    def test_truncated_coverage_is_not_claimable(self) -> None:
        cov = CoverageDeclaration(scope="dossier", status="complete", truncated=True, omitted_count=0)
        assert cov.absence_claimable is False

    def test_partial_coverage_is_not_claimable(self) -> None:
        cov = CoverageDeclaration(scope="dossier", status="partial", truncated=False, omitted_count=0)
        assert cov.absence_claimable is False


@pytest.mark.unit
class TestFacetConflationDefense:
    """Verify defense against treating unobserved or undeclared empty facets as 0 occurrences."""

    def test_undeclared_empty_facet_forces_unknown(self) -> None:
        service = StandardDifferentialFacetService()
        left = {"id": "ev:1", "assembly": []}  # empty list with no facet_availability declaration
        right = {"id": "ev:2", "assembly": ["push rbp", "ret"]}
        report = service.compare_observations(left, right)
        dim_map = {d.dimension: d for d in report.dimensions}
        assert "assembly" in dim_map
        assert dim_map["assembly"].status == "unknown"
        assert dim_map["assembly"].left_digest is None
        assert dim_map["assembly"].left_count is None
        assert report.overall_status == "unknown"


@pytest.mark.unit
class TestObservedAbsenceParity:
    """Verify that explicitly declared empty facets on both sides yield unchanged status."""

    def test_declared_available_empty_both_sides_is_unchanged(self) -> None:
        service = StandardDifferentialFacetService()
        left = {
            "id": "ev:1",
            "facet_availability": {"assembly": {"available": True}},
            "assembly": [],
            "coverage": {"scope": "dossier", "status": "complete"},
        }
        right = {
            "id": "ev:2",
            "facet_availability": {"assembly": {"available": True}},
            "assembly": [],
            "coverage": {"scope": "dossier", "status": "complete"},
        }
        report = service.compare_observations(left, right)
        dim_map = {d.dimension: d for d in report.dimensions}
        assert dim_map["assembly"].status == "unchanged"
        assert dim_map["assembly"].left_count == 0
        assert dim_map["assembly"].right_count == 0


@pytest.mark.unit
class TestProviderDecoupling:
    """Verify cross-provider representation decoupling."""

    def test_different_providers_records_limitation_not_contradiction(self) -> None:
        service = StandardDifferentialFacetService()
        left = {
            "id": "ev:1",
            "provider": "ghidra",
            "assembly": ["push %rbp"],
            "coverage": {"scope": "dossier", "status": "complete"},
        }
        right = {
            "id": "ev:2",
            "provider": "hopper",
            "assembly": ["push rbp"],
            "coverage": {"scope": "dossier", "status": "complete"},
        }
        report = service.compare_observations(left, right, providers_differ=True)
        assert any("providersDiffer" in limit for limit in report.limitations)
        dim_map = {d.dimension: d for d in report.dimensions}
        assert any("providersDiffer" in limit for limit in dim_map["assembly"].limitations)


@pytest.mark.unit
class TestDigestDeterminism:
    """Verify that identical inputs produce identical report IDs across repeated runs."""

    def test_identical_inputs_produce_identical_report_id(self) -> None:
        service = StandardDifferentialFacetService()
        left = {
            "id": "ev:1",
            "identity": {"name": "target_func", "address": "0x401000"},
            "coverage": {"scope": "dossier", "status": "complete"},
        }
        right = {
            "id": "ev:2",
            "identity": {"name": "target_func", "address": "0x401000"},
            "coverage": {"scope": "dossier", "status": "complete"},
        }
        first_report = service.compare_observations(left, right)
        for _ in range(50):
            rep = service.compare_observations(left, right)
            assert rep.report_id == first_report.report_id
            assert rep.summary_digest == first_report.summary_digest


# -----------------------------------------------------------------------------
# Block 4 — CLI Seams & Ecosystem Integration
# -----------------------------------------------------------------------------

@pytest.mark.unit
class TestFacetCLISeams:
    """Verify that all headless Click CLI subcommands execute cleanly and exit 0."""

    def test_all_subcommands_exit_zero(self, tmp_path: Path) -> None:
        runner = CliRunner()
        left_file = tmp_path / "left.json"
        right_file = tmp_path / "right.json"
        cov_file = tmp_path / "coverage.json"
        report_file = tmp_path / "report.json"

        left_data = {
            "id": "ev:left",
            "coverage": {"scope": "dossier", "status": "complete"},
            "identity": {"name": "func_a"},
        }
        right_data = {
            "id": "ev:right",
            "coverage": {"scope": "dossier", "status": "complete"},
            "identity": {"name": "func_a"},
        }
        cov_data = {"scope": "dossier", "status": "complete", "truncated": False, "omitted_count": 0}

        left_file.write_text(json.dumps(left_data), encoding="utf-8")
        right_file.write_text(json.dumps(right_data), encoding="utf-8")
        cov_file.write_text(json.dumps(cov_data), encoding="utf-8")

        # 1. Compare subcommand
        res_compare = runner.invoke(facet_group, ["compare", str(left_file), str(right_file), "--format", "json"])
        assert res_compare.exit_code == 0
        rep_dict = json.loads(res_compare.output)
        assert rep_dict["overall_status"] == "unchanged"
        report_file.write_text(res_compare.output, encoding="utf-8")

        # 2. Claim-absence subcommand
        res_absence = runner.invoke(facet_group, ["claim-absence", str(cov_file)])
        assert res_absence.exit_code == 0
        abs_dict = json.loads(res_absence.output)
        assert abs_dict["absence_claimable"] is True

        # 3. Verify subcommand
        res_verify = runner.invoke(facet_group, ["verify", str(report_file), "--strict"])
        assert res_verify.exit_code == 0
        assert "Verified report integrity" in res_verify.output

        # 4. Export subcommand
        res_export = runner.invoke(facet_group, ["export", str(report_file)])
        assert res_export.exit_code == 0
        exported = json.loads(res_export.output)
        assert exported["report_id"] == rep_dict["report_id"]


@pytest.mark.unit
@pytest.mark.asyncio
class TestEcosystemHygiene:
    """Verify skill validation, SkillCardParser, and Rule 40 dual-file Knowledge Item integrity."""

    async def test_skills_hygiene_and_ki_dual_file_integrity(self, skill_dir: Path, ki_dir: Path) -> None:
        # Validate skill
        report = await SkillValidator.validate_async(skill_dir)
        assert report.valid is True, f"Skill validation failed: {report.errors}"

        # Parse skill card
        parsed = SkillCardParser.parse_directory(skill_dir)
        assert parsed is not None
        assert parsed.name == "differential-facet-verifier"
        assert len(parsed.stages) >= 2
        assert len(parsed.anti_patterns) >= 1
        assert len(parsed.invariants) >= 1

        # Check Knowledge Item dual-file integrity
        meta_file = ki_dir / "metadata.json"
        summary_file = ki_dir / "summary.md"
        assert meta_file.exists()
        assert summary_file.exists()

        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        assert meta["id"] == "ki-rea-facet-availability-semantics"
        assert len(meta.get("claims", [])) >= 3
        for claim in meta["claims"]:
            assert "claim_id" in claim
            assert "assertion" in claim
            assert "evidence_quote" in claim
            assert "source_file" in claim

        summary_text = summary_file.read_text(encoding="utf-8")
        assert "Ground-Truth Mental Models" in summary_text
        assert "Anti-Pattern Defenses" in summary_text
