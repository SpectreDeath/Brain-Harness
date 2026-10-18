"""Comprehensive contract test suite for Reconstruction Obligation Ledger (ROL)

Validates slotted/frozen dataclass immutability (Rule 12 & Rule 43), digest determinism,
8-state FSM transitions, facet availability semantics, closure proof guarantees,
skill hygiene, and headless Click CLI introspection (Rule 10).
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.creator.skills import SkillValidator
from harness.services.reconstruction_obligation import (
    CanonicalEvidence,
    FacetAvailability,
    ObligationItem,
    ReconstructionProof,
    StandardReconstructionObligationService,
    canonicalize_json,
    compute_canonical_hash,
)
from harness.commands.rol import rol_group
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser
from plugins.memory_and_epistemics.skill_knowledge_graph.models import SkillNode


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture
def skill_dir(repo_root: Path) -> Path:
    target = repo_root / ".agents" / "skills" / "reconstruction-obligation-ledger"
    assert target.exists(), f"Skill directory missing: {target}"
    return target


@pytest.fixture
def ki_dir(repo_root: Path) -> Path:
    target = repo_root / ".harness" / "knowledge" / "ki-rea-reconstruction-obligations"
    assert target.exists(), f"Knowledge Item directory missing: {target}"
    return target


# -----------------------------------------------------------------------------
# Contract 1: Slotted & Frozen Dataclass Immutability (Rule 12 & Rule 43)
# -----------------------------------------------------------------------------

@pytest.mark.unit
class TestSlottedFrozenImmutability:
    """Verify that domain dataclasses enforce slots=True and frozen=True."""

    def test_facet_availability_immutability(self) -> None:
        facet = FacetAvailability(available=True)
        with pytest.raises((AttributeError, TypeError)):
            facet.available = False  # type: ignore

    def test_canonical_evidence_immutability(self) -> None:
        evidence = CanonicalEvidence(
            evidence_id="ev:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            provider_id="ghidra",
            subject_format="elf",
            normalized_result="{}",
            raw_result=None,
            facet_availability=(),
            timestamp="2026-10-18T00:00:00Z",
        )
        with pytest.raises((AttributeError, TypeError)):
            evidence.provider_id = "rizin"  # type: ignore

    def test_obligation_item_immutability(self) -> None:
        item = ObligationItem(
            obligation_id="ob_cli_0001",
            layer="cli",
            case_kind="positive",
            description="CLI flag parsing",
            disposition="unowned",
            evidence_ids=(),
        )
        with pytest.raises((AttributeError, TypeError)):
            item.disposition = "verified"  # type: ignore

    def test_reconstruction_proof_immutability(self) -> None:
        proof = ReconstructionProof(
            closure_digest="sha256:abcdef",
            total_obligations=10,
            verified_count=10,
            unowned_count=0,
            contradicted_count=0,
            is_closed=True,
        )
        with pytest.raises((AttributeError, TypeError)):
            proof.is_closed = False  # type: ignore


# -----------------------------------------------------------------------------
# Contract 2: Canonical Digest Determinism
# -----------------------------------------------------------------------------

@pytest.mark.unit
class TestDigestDeterminism:
    """Verify reproducible SHA-256 evidence digests across varying key orderings."""

    def test_digest_stability_across_runs(self) -> None:
        service = StandardReconstructionObligationService()
        payload_a = {"z_symbol": "main", "a_offset": 4096, "nested": {"b": 2, "a": 1}}
        payload_b = {"a_offset": 4096, "nested": {"a": 1, "b": 2}, "z_symbol": "main"}

        ev1 = service.ingest_evidence(
            provider_id="wakaru",
            subject_format="javascript",
            normalized_result=payload_a,
        )
        ev2 = service.ingest_evidence(
            provider_id="wakaru",
            subject_format="javascript",
            normalized_result=payload_b,
        )
        assert ev1.evidence_id == ev2.evidence_id
        assert ev1.evidence_id.startswith("ev:")
        assert len(ev1.evidence_id) == 3 + 64  # "ev:" + 64-char hex

    def test_distinct_payloads_produce_distinct_digests(self) -> None:
        service = StandardReconstructionObligationService()
        ev1 = service.ingest_evidence(provider_id="ghidra", subject_format="elf", normalized_result={"fn": "alpha"})
        ev2 = service.ingest_evidence(provider_id="ghidra", subject_format="elf", normalized_result={"fn": "beta"})
        assert ev1.evidence_id != ev2.evidence_id


# -----------------------------------------------------------------------------
# Contract 3: 8-State FSM State Transitions
# -----------------------------------------------------------------------------

@pytest.mark.unit
class TestFsmTransitions:
    """Verify valid state progression and guard condition enforcement."""

    def test_valid_progression_lifecycle(self) -> None:
        service = StandardReconstructionObligationService()
        ev = service.ingest_evidence("ghidra", "elf", {"symbol": "decrypt_key"})

        # Step 1: Register (unowned)
        ob = service.add_obligation("ob_crypto_01", "native-abi", "positive", "AES-256 decryption")
        assert ob.disposition == "unowned"

        # Step 2: Characterize (requires evidence)
        ob = service.transition_disposition("ob_crypto_01", "characterized", evidence_ids=[ev.evidence_id])
        assert ob.disposition == "characterized"
        assert ev.evidence_id in ob.evidence_ids

        # Step 3: Implement (requires owner_path)
        ob = service.transition_disposition("ob_crypto_01", "implemented", owner_path="src/crypto/aes.py")
        assert ob.disposition == "implemented"
        assert ob.owner_path == "src/crypto/aes.py"

        # Step 4: Verify
        ob = service.transition_disposition("ob_crypto_01", "verified")
        assert ob.disposition == "verified"

    def test_characterized_requires_evidence(self) -> None:
        service = StandardReconstructionObligationService()
        service.add_obligation("ob_01", "cli", "positive", "Command line help")
        with pytest.raises(ValueError, match="at least 1 evidence record"):
            service.transition_disposition("ob_01", "characterized")

    def test_implemented_requires_owner_path(self) -> None:
        service = StandardReconstructionObligationService()
        ev = service.ingest_evidence("ghidra", "elf", {"data": 1})
        service.add_obligation("ob_01", "cli", "positive", "Help", evidence_ids=[ev.evidence_id])
        service.transition_disposition("ob_01", "characterized", evidence_ids=[ev.evidence_id])
        with pytest.raises(ValueError, match="owner_path"):
            service.transition_disposition("ob_01", "implemented")

    def test_invalid_transition_rejected(self) -> None:
        service = StandardReconstructionObligationService()
        service.add_obligation("ob_01", "cli", "positive", "Help")
        with pytest.raises(ValueError, match="Invalid FSM transition"):
            # Cannot jump directly from unowned to verified
            service.transition_disposition("ob_01", "verified")


# -----------------------------------------------------------------------------
# Contract 4: Facet Availability Semantics
# -----------------------------------------------------------------------------

@pytest.mark.unit
class TestFacetAvailabilitySemantics:
    """Verify that unobserved facets are never treated as empty collections."""

    def test_unobserved_facet_requires_reason(self) -> None:
        facet = FacetAvailability(available=False)
        assert facet.available is False
        assert facet.reason is not None
        assert "not observed" in facet.reason

    def test_observed_empty_facet(self) -> None:
        facet = FacetAvailability(available=True)
        assert facet.available is True
        assert facet.reason is None


# -----------------------------------------------------------------------------
# Contract 5: Closure Proof Invariants
# -----------------------------------------------------------------------------

@pytest.mark.unit
class TestClosureProofInvariants:
    """Verify cryptographic closure rules and strict verification gates."""

    def test_open_ledger_cannot_claim_closure(self) -> None:
        service = StandardReconstructionObligationService()
        service.add_obligation("ob_01", "protocol", "positive", "Handshake")
        proof = service.verify_ledger(strict=False)
        assert proof.is_closed is False
        assert proof.unowned_count == 1

        with pytest.raises(ValueError, match="closure check failed"):
            service.verify_ledger(strict=True)

    def test_all_verified_closes_ledger(self) -> None:
        service = StandardReconstructionObligationService()
        ev = service.ingest_evidence("rizin", "pe", {"sections": [".text"]})
        service.add_obligation("ob_01", "protocol", "positive", "Handshake")
        service.transition_disposition("ob_01", "characterized", evidence_ids=[ev.evidence_id])
        service.transition_disposition("ob_01", "implemented", owner_path="src/proto/handshake.py")
        service.transition_disposition("ob_01", "verified")

        proof = service.verify_ledger(strict=True)
        assert proof.is_closed is True
        assert proof.total_obligations == 1
        assert proof.verified_count == 1
        assert proof.unowned_count == 0
        assert len(proof.closure_digest) == 64


# -----------------------------------------------------------------------------
# Contract 6: Skill Package Hygiene & Craft Standards
# -----------------------------------------------------------------------------

@pytest.mark.unit
class TestSkillPackageHygiene:
    """Verify structural hygiene, YAML frontmatter, CARD.md, and parser compatibility."""

    def test_required_files_exist(self, skill_dir: Path) -> None:
        assert (skill_dir / "SKILL.md").exists()
        assert (skill_dir / "CARD.md").exists()
        assert (skill_dir / "config.default.yaml").exists()
        assert (skill_dir / "references" / "evidence-schema.md").exists()
        assert (skill_dir / "references" / "obligation-states.md").exists()
        assert (skill_dir / "scripts" / "rol_engine.py").exists()

    @pytest.mark.asyncio
    async def test_skill_validator_passes(self, skill_dir: Path) -> None:
        report = await SkillValidator.validate_async(skill_dir)
        assert report.valid is True, f"SkillValidator failed: {report.errors}"
        for check in report.checks:
            assert check.passed is True, f"Check failed: {check.name} - {check.message}"

    def test_card_parser_and_pillars(self, skill_dir: Path) -> None:
        node = SkillCardParser.parse_directory(skill_dir)
        assert isinstance(node, SkillNode)
        assert node.name == "reconstruction-obligation-ledger"
        assert len(node.stages) >= 5, f"Expected >= 5 stages, found {len(node.stages)}"
        assert len(node.anti_patterns) >= 4, f"Expected >= 4 anti-patterns, found {len(node.anti_patterns)}"
        assert len(node.invariants) >= 5, f"Expected >= 5 invariants, found {len(node.invariants)}"
        assert all(inv.is_blocking for inv in node.invariants), "All invariants must be blocking"

    def test_frontmatter_budget_and_negative_boundary(self, skill_dir: Path) -> None:
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        from harness.services.skill_parser.frontmatter import extract_frontmatter
        frontmatter, _ = extract_frontmatter(skill_text)
        desc = frontmatter.get("description", "")
        assert 100 <= len(desc) <= 350, f"Description length {len(desc)} not in [100, 350]"
        assert "Do not use for" in desc, "Must contain explicit negative boundary"


# -----------------------------------------------------------------------------
# Contract 7: Headless Click CLI Seams (Rule 10)
# -----------------------------------------------------------------------------

@pytest.mark.unit
class TestClickCliSeams:
    """Verify headless Click CLI subcommands."""

    def test_cli_ingest_and_add_and_verify(self, tmp_path: Path) -> None:
        runner = CliRunner()
        ledger_file = tmp_path / "ledger.json"
        evidence_file = tmp_path / "evidence.json"
        evidence_file.write_text(json.dumps({"procedure": "init", "subroutines": 4}), encoding="utf-8")

        # Ingest
        res_ingest = runner.invoke(rol_group, ["ingest", str(evidence_file), "--ledger", str(ledger_file), "--provider", "ghidra"])
        assert res_ingest.exit_code == 0
        ev_id = res_ingest.output.strip()
        assert ev_id.startswith("ev:")

        # Add Obligation
        res_add = runner.invoke(rol_group, ["obligation", "add", "Initialization routine", "--ledger", str(ledger_file), "--layer", "process"])
        assert res_add.exit_code == 0
        assert "Registered obligation" in res_add.output

        # Verify (Open)
        res_verify = runner.invoke(rol_group, ["verify", str(ledger_file), "--json-output"])
        assert res_verify.exit_code == 0
        data = json.loads(res_verify.output)
        assert data["is_closed"] is False
        assert data["unowned_count"] == 1

        # Export
        res_export = runner.invoke(rol_group, ["export", str(ledger_file)])
        assert res_export.exit_code == 0
        cert = json.loads(res_export.output)
        assert cert["proof"]["total_obligations"] == 1
        assert ev_id in cert["evidence"]


# -----------------------------------------------------------------------------
# Contract 8: Knowledge Item Dual-File Integrity (Rule 40)
# -----------------------------------------------------------------------------

@pytest.mark.unit
class TestKnowledgeItemIntegrity:
    """Verify Rule 40 dual-file Knowledge Item format and isnad lineage."""

    def test_dual_file_vault_structure(self, ki_dir: Path) -> None:
        meta_file = ki_dir / "metadata.json"
        summary_file = ki_dir / "summary.md"
        assert meta_file.exists(), "metadata.json missing"
        assert summary_file.exists(), "summary.md missing"

        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        assert meta["id"] == "ki-rea-reconstruction-obligations"
        assert len(meta.get("claims", [])) >= 3

        for claim in meta["claims"]:
            assert "claim_id" in claim
            assert "assertion" in claim
            assert "evidence_quote" in claim
            assert "source_file" in claim

        summary_text = summary_file.read_text(encoding="utf-8")
        assert "Ground-Truth Mental Models" in summary_text
        assert "Anti-Pattern Defenses" in summary_text
