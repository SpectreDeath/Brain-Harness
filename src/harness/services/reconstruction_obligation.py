"""Reconstruction Obligation Ledger Service Protocol, Models, and ServiceKey.

Elevates reverse-engineering evidence canonicalization, 8-state disposition FSMs,
and cryptographic reconstruction closure proofs into an IoC micro-kernel service seam.
Synthesized from REA (morluto/rea) evidence and reconstruction obligation ledgers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceContext, ServiceKey

# -----------------------------------------------------------------------------
# Architectural Constants & Enums
# -----------------------------------------------------------------------------

VALID_LAYERS: frozenset[str] = frozenset({
    "cli",
    "protocol",
    "electron",
    "persistence",
    "process",
    "runtime",
    "packaging",
    "native-abi",
    "application",
    "other",
})

VALID_CASE_KINDS: frozenset[str] = frozenset({
    "positive",
    "negative",
})

VALID_DISPOSITIONS: frozenset[str] = frozenset({
    "unowned",
    "characterized",
    "implemented",
    "verified",
    "contradicted",
    "blocked",
    "out-of-scope",
    "unknown",
})

# Permitted FSM transitions
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "unowned": frozenset({"characterized", "blocked", "out-of-scope", "unknown"}),
    "characterized": frozenset({"implemented", "contradicted", "blocked", "out-of-scope", "unknown"}),
    "implemented": frozenset({"verified", "contradicted", "blocked", "unknown"}),
    "verified": frozenset({"contradicted", "unknown"}),
    "contradicted": frozenset({"characterized", "blocked", "out-of-scope", "unknown"}),
    "blocked": frozenset({"unowned", "characterized", "unknown"}),
    "out-of-scope": frozenset({"unowned", "unknown"}),
    "unknown": frozenset({"unowned", "characterized"}),
}


# -----------------------------------------------------------------------------
# Slotted & Frozen Dataclass Domain Models (Rule 12 & Rule 43)
# -----------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class FacetAvailability:
    """Explicit facet observation availability status."""

    available: bool
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.available and not self.reason:
            object.__setattr__(self, "reason", "Facet was not observed during provider execution")


@dataclass(slots=True, frozen=True)
class CanonicalEvidence:
    """Immutable, content-addressed evidence record keyed by SHA-256 digest."""

    evidence_id: str
    provider_id: str
    subject_format: str
    normalized_result: str
    raw_result: str | None
    facet_availability: tuple[tuple[str, FacetAvailability], ...]
    timestamp: str

    def __post_init__(self) -> None:
        if not self.evidence_id.startswith("ev:"):
            raise ValueError(f"Evidence ID must start with 'ev:', got {self.evidence_id}")


@dataclass(slots=True, frozen=True)
class ObligationItem:
    """Reconstruction obligation tracking a behavioral surface through the 8-state FSM."""

    obligation_id: str
    layer: str
    case_kind: str
    description: str
    disposition: str
    evidence_ids: tuple[str, ...]
    owner_path: str | None = None
    owner_sha256: str | None = None

    def __post_init__(self) -> None:
        if self.layer not in VALID_LAYERS:
            raise ValueError(f"Invalid layer '{self.layer}'. Must be one of {sorted(VALID_LAYERS)}")
        if self.case_kind not in VALID_CASE_KINDS:
            raise ValueError(f"Invalid case_kind '{self.case_kind}'. Must be one of {sorted(VALID_CASE_KINDS)}")
        if self.disposition not in VALID_DISPOSITIONS:
            raise ValueError(f"Invalid disposition '{self.disposition}'. Must be one of {sorted(VALID_DISPOSITIONS)}")


@dataclass(slots=True, frozen=True)
class ReconstructionProof:
    """Cryptographic certificate proving closure and verification of reconstruction obligations."""

    closure_digest: str
    total_obligations: int
    verified_count: int
    unowned_count: int
    contradicted_count: int
    is_closed: bool


# -----------------------------------------------------------------------------
# Service Protocol & ServiceKey
# -----------------------------------------------------------------------------

@runtime_checkable
class ReconstructionObligationService(Protocol):
    """Protocol for managing canonical evidence records and obligation ledgers."""

    def ingest_evidence(
        self,
        provider_id: str,
        subject_format: str,
        normalized_result: dict[str, Any] | str,
        raw_result: str | None = None,
        facet_availability: dict[str, FacetAvailability] | None = None,
        timestamp: str | None = None,
    ) -> CanonicalEvidence:
        """Digest tool observation, create immutable CanonicalEvidence, and record in ledger."""
        ...

    def add_obligation(
        self,
        obligation_id: str,
        layer: str,
        case_kind: str,
        description: str,
        disposition: str = "unowned",
        evidence_ids: list[str] | None = None,
        owner_path: str | None = None,
        owner_sha256: str | None = None,
    ) -> ObligationItem:
        """Register a new behavioral obligation surface."""
        ...

    def transition_disposition(
        self,
        obligation_id: str,
        new_disposition: str,
        evidence_ids: list[str] | None = None,
        owner_path: str | None = None,
        owner_sha256: str | None = None,
    ) -> ObligationItem:
        """Transition an obligation along the valid 8-state FSM."""
        ...

    def verify_ledger(self, strict: bool = False) -> ReconstructionProof:
        """Compute the closure digest and evaluate reconstruction completion."""
        ...

    def export_certificate(self) -> dict[str, Any]:
        """Export machine-readable JSON reconstruction certificate."""
        ...


RECONSTRUCTION_OBLIGATION_SERVICE_KEY: ServiceKey[ReconstructionObligationService] = ServiceKey(
    "service.reconstruction_obligation"
)


def resolve_reconstruction_obligation(
    ctx: ServiceContext,
) -> ReconstructionObligationService | None:
    """Resolve ReconstructionObligationService from context if registered."""
    return ctx.optional(RECONSTRUCTION_OBLIGATION_SERVICE_KEY)


# -----------------------------------------------------------------------------
# Canonical Serialization & Standard Implementation
# -----------------------------------------------------------------------------

def canonicalize_json(data: Any) -> str:
    """Produce deterministic JSON with sorted keys and no extraneous whitespace."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_canonical_hash(payload_str: str) -> str:
    """Compute SHA-256 hexadecimal digest from canonical UTF-8 payload."""
    return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()


class StandardReconstructionObligationService:
    """Standard in-memory implementation of ReconstructionObligationService."""

    def __init__(self) -> None:
        self._evidence: dict[str, CanonicalEvidence] = {}
        self._obligations: dict[str, ObligationItem] = {}

    def ingest_evidence(
        self,
        provider_id: str,
        subject_format: str,
        normalized_result: dict[str, Any] | str,
        raw_result: str | None = None,
        facet_availability: dict[str, FacetAvailability] | None = None,
        timestamp: str | None = None,
    ) -> CanonicalEvidence:
        normalized_str = (
            normalized_result
            if isinstance(normalized_result, str)
            else canonicalize_json(normalized_result)
        )

        facets_dict = facet_availability or {}
        # Deterministically sort facets by key
        sorted_facets: tuple[tuple[str, FacetAvailability], ...] = tuple(
            sorted(facets_dict.items(), key=lambda item: item[0])
        )

        iso_timestamp = timestamp or "2026-10-18T00:00:00Z"

        # Canonical hashing payload
        hash_payload = {
            "provider_id": provider_id,
            "subject_format": subject_format,
            "normalized_result": normalized_str,
            "facet_availability": {
                k: {"available": v.available, "reason": v.reason}
                for k, v in sorted_facets
            },
        }
        canonical_str = canonicalize_json(hash_payload)
        digest = compute_canonical_hash(canonical_str)
        evidence_id = f"ev:{digest}"

        record = CanonicalEvidence(
            evidence_id=evidence_id,
            provider_id=provider_id,
            subject_format=subject_format,
            normalized_result=normalized_str,
            raw_result=raw_result,
            facet_availability=sorted_facets,
            timestamp=iso_timestamp,
        )
        self._evidence[evidence_id] = record
        return record

    def add_obligation(
        self,
        obligation_id: str,
        layer: str,
        case_kind: str,
        description: str,
        disposition: str = "unowned",
        evidence_ids: list[str] | None = None,
        owner_path: str | None = None,
        owner_sha256: str | None = None,
    ) -> ObligationItem:
        if obligation_id in self._obligations:
            raise ValueError(f"Obligation with ID '{obligation_id}' already registered")

        ev_tuple = tuple(evidence_ids or [])
        item = ObligationItem(
            obligation_id=obligation_id,
            layer=layer,
            case_kind=case_kind,
            description=description,
            disposition=disposition,
            evidence_ids=ev_tuple,
            owner_path=owner_path,
            owner_sha256=owner_sha256,
        )
        self._obligations[obligation_id] = item
        return item

    def transition_disposition(
        self,
        obligation_id: str,
        new_disposition: str,
        evidence_ids: list[str] | None = None,
        owner_path: str | None = None,
        owner_sha256: str | None = None,
    ) -> ObligationItem:
        if obligation_id not in self._obligations:
            raise KeyError(f"Obligation '{obligation_id}' not found in ledger")

        current = self._obligations[obligation_id]
        if new_disposition not in VALID_DISPOSITIONS:
            raise ValueError(f"Invalid target disposition '{new_disposition}'")

        allowed = ALLOWED_TRANSITIONS.get(current.disposition, frozenset())
        if new_disposition not in allowed:
            raise ValueError(
                f"Invalid FSM transition: cannot transition obligation '{obligation_id}' "
                f"from '{current.disposition}' to '{new_disposition}'."
            )

        merged_ev = list(current.evidence_ids)
        if evidence_ids:
            for eid in evidence_ids:
                if eid not in merged_ev:
                    merged_ev.append(eid)

        # Invariant checks
        if new_disposition == "characterized" and not merged_ev:
            raise ValueError("Characterized obligations must be linked to at least 1 evidence record")
        if new_disposition == "implemented" and not (owner_path or current.owner_path):
            raise ValueError("Implemented obligations must declare an owner_path")

        updated = ObligationItem(
            obligation_id=current.obligation_id,
            layer=current.layer,
            case_kind=current.case_kind,
            description=current.description,
            disposition=new_disposition,
            evidence_ids=tuple(merged_ev),
            owner_path=owner_path or current.owner_path,
            owner_sha256=owner_sha256 or current.owner_sha256,
        )
        self._obligations[obligation_id] = updated
        return updated

    def verify_ledger(self, strict: bool = False) -> ReconstructionProof:
        total = len(self._obligations)
        verified = sum(1 for o in self._obligations.values() if o.disposition == "verified")
        unowned = sum(1 for o in self._obligations.values() if o.disposition == "unowned")
        contradicted = sum(1 for o in self._obligations.values() if o.disposition == "contradicted")

        is_closed = total > 0 and unowned == 0 and contradicted == 0

        # Deterministic closure digest over sorted obligations
        serialized_items = [
            {
                "id": o.obligation_id,
                "layer": o.layer,
                "case_kind": o.case_kind,
                "disposition": o.disposition,
                "evidence_ids": list(o.evidence_ids),
                "owner_path": o.owner_path,
                "owner_sha256": o.owner_sha256,
            }
            for o in sorted(self._obligations.values(), key=lambda x: x.obligation_id)
        ]
        closure_digest = compute_canonical_hash(canonicalize_json(serialized_items))

        proof = ReconstructionProof(
            closure_digest=closure_digest,
            total_obligations=total,
            verified_count=verified,
            unowned_count=unowned,
            contradicted_count=contradicted,
            is_closed=is_closed,
        )

        if strict and not is_closed:
            raise ValueError(
                f"Reconstruction ledger closure check failed: {unowned} unowned, "
                f"{contradicted} contradicted out of {total} total obligations."
            )

        return proof

    def load_from_dict(self, data: dict[str, Any]) -> None:
        """Load state from exported certificate dict."""
        for eid, ev in data.get("evidence", {}).items():
            facets = tuple(
                (k, FacetAvailability(available=v.get("available", False), reason=v.get("reason")))
                for k, v in ev.get("facet_availability", {}).items()
            )
            record = CanonicalEvidence(
                evidence_id=ev.get("id", eid),
                provider_id=ev["provider_id"],
                subject_format=ev["subject_format"],
                normalized_result=ev.get("normalized_result", "{}"),
                raw_result=ev.get("raw_result"),
                facet_availability=facets,
                timestamp=ev.get("timestamp", "2026-10-18T00:00:00Z"),
            )
            self._evidence[record.evidence_id] = record

        for ob in data.get("obligations", []):
            item = ObligationItem(
                obligation_id=ob["id"],
                layer=ob["layer"],
                case_kind=ob["case_kind"],
                description=ob["description"],
                disposition=ob.get("disposition", "unowned"),
                evidence_ids=tuple(ob.get("evidence_ids", [])),
                owner_path=ob.get("owner_path"),
                owner_sha256=ob.get("owner_sha256"),
            )
            self._obligations[item.obligation_id] = item

    def export_certificate(self) -> dict[str, Any]:
        proof = self.verify_ledger(strict=False)
        return {
            "version": "1.0.0",
            "proof": {
                "closure_digest": proof.closure_digest,
                "is_closed": proof.is_closed,
                "total_obligations": proof.total_obligations,
                "verified_count": proof.verified_count,
                "unowned_count": proof.unowned_count,
                "contradicted_count": proof.contradicted_count,
            },
            "obligations": [
                {
                    "id": o.obligation_id,
                    "layer": o.layer,
                    "case_kind": o.case_kind,
                    "description": o.description,
                    "disposition": o.disposition,
                    "evidence_ids": list(o.evidence_ids),
                    "owner_path": o.owner_path,
                    "owner_sha256": o.owner_sha256,
                }
                for o in sorted(self._obligations.values(), key=lambda x: x.obligation_id)
            ],
            "evidence": {
                eid: {
                    "id": ev.evidence_id,
                    "provider_id": ev.provider_id,
                    "subject_format": ev.subject_format,
                    "normalized_result": ev.normalized_result,
                    "raw_result": ev.raw_result,
                    "timestamp": ev.timestamp,
                    "facet_availability": {
                        k: {"available": v.available, "reason": v.reason}
                        for k, v in ev.facet_availability
                    },
                }
                for eid, ev in sorted(self._evidence.items(), key=lambda x: x[0])
            },
        }

