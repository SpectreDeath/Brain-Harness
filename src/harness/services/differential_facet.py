"""Differential Facet Verifier & Availability Semantics Service Protocol, Models, and ServiceKey.

Elevates multi-provider evidence dossier comparisons, facet availability semantics,
absence claimability gates, and 3-valued differential outcome synthesis into an IoC micro-kernel service seam.
Synthesized from REA (morluto/rea) function comparison dimensions and comparison semantics.
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

VALID_DIMENSIONS: frozenset[str] = frozenset({
    "identity",
    "pseudocode",
    "assembly",
    "comments",
    "calls",
    "references",
    "strings_names",
    "cfg",
})

VALID_STATUSES: frozenset[str] = frozenset({
    "unchanged",
    "changed",
    "unknown",
})

VALID_CONCLUSION_KINDS: frozenset[str] = frozenset({
    "derived_relationship",
    "contradiction",
    "unresolved",
})

VALID_COVERAGE_STATUSES: frozenset[str] = frozenset({
    "complete",
    "unknown",
    "partial",
})


# -----------------------------------------------------------------------------
# Canonical Serialization & Hashing
# -----------------------------------------------------------------------------

def canonicalize_json(data: Any) -> str:
    """Produce deterministic JSON with sorted keys and no extraneous whitespace."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_canonical_hash(payload_str: str) -> str:
    """Compute SHA-256 hexadecimal digest from canonical UTF-8 payload."""
    return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()


# -----------------------------------------------------------------------------
# Slotted & Frozen Dataclass Domain Models (Rule 12 & Rule 43)
# -----------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class FacetAvailability:
    """Explicit facet observation availability status."""

    available: bool
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.available and not (self.reason and self.reason.strip()):
            raise ValueError("Facet marked unavailable must declare a non-empty reason.")


# Alias for backward-compatible/unambiguous imports
DifferentialFacetAvailability = FacetAvailability


@dataclass(slots=True, frozen=True)
class CoverageDeclaration:
    """Declaration of traversal coverage across a container, entry set, or dossier."""

    scope: str        # "root" | "container-entries" | "dossier"
    status: str       # "complete" | "unknown" | "partial"
    truncated: bool = False
    omitted_count: int = 0

    def __post_init__(self) -> None:
        if self.status not in VALID_COVERAGE_STATUSES:
            raise ValueError(
                f"Invalid coverage status: {self.status!r}. Must be one of {sorted(VALID_COVERAGE_STATUSES)}"
            )
        if self.omitted_count < 0:
            raise ValueError("omitted_count must be >= 0")

    @property
    def absence_claimable(self) -> bool:
        """Formal absence claimability rule (REA comparisonSemantics.ts L3-L11)."""
        return self.status == "complete" and not self.truncated and self.omitted_count == 0


@dataclass(slots=True, frozen=True)
class DimensionOutcome:
    """Outcome of evaluating an individual comparison dimension across two observations."""

    dimension: str       # Must be in VALID_DIMENSIONS
    status: str          # "unchanged" | "changed" | "unknown"
    conclusion_kind: str # "derived_relationship" | "contradiction" | "unresolved"
    left_digest: str | None
    right_digest: str | None
    left_count: int | None
    right_count: int | None
    limitations: tuple[str, ...] = ()
    evidence_links: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.dimension not in VALID_DIMENSIONS:
            raise ValueError(f"Unknown dimension: {self.dimension!r}. Must be one of {sorted(VALID_DIMENSIONS)}")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}. Must be one of {sorted(VALID_STATUSES)}")
        if self.conclusion_kind not in VALID_CONCLUSION_KINDS:
            raise ValueError(
                f"Invalid conclusion_kind: {self.conclusion_kind!r}. Must be one of {sorted(VALID_CONCLUSION_KINDS)}"
            )

        # Invariant: unknown dimension must carry null digests and null counts
        if self.status == "unknown":
            if self.left_digest is not None or self.right_digest is not None:
                raise ValueError("unknown dimension must not carry digests")
            if self.left_count is not None or self.right_count is not None:
                raise ValueError("unknown dimension must carry null counts")


@dataclass(slots=True, frozen=True)
class DifferentialReport:
    """Differential comparison report between two multi-provider observation dossiers."""

    report_id: str          # rep:<sha256>
    overall_status: str     # "unchanged" | "changed" | "unknown"
    left_evidence_id: str   # ev:<sha256>
    right_evidence_id: str  # ev:<sha256>
    dimensions: tuple[DimensionOutcome, ...]
    summary_digest: str     # SHA-256 of canonical serialized dimensions
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.report_id.startswith("rep:"):
            raise ValueError(f"report_id must be prefixed rep:<sha256>, got {self.report_id!r}")
        if self.overall_status not in VALID_STATUSES:
            raise ValueError(f"Invalid overall_status: {self.overall_status!r}")

        # Strictest dimension status propagates to overall
        statuses = {d.status for d in self.dimensions}
        if "unknown" in statuses and self.overall_status == "unchanged":
            raise ValueError("overall_status cannot be 'unchanged' when any dimension is 'unknown'")


# -----------------------------------------------------------------------------
# Service Protocol & ServiceKey
# -----------------------------------------------------------------------------

@runtime_checkable
class DifferentialFacetService(Protocol):
    """Protocol for differential facet verification and availability semantics."""

    def validate_absence_claim(self, coverage: CoverageDeclaration) -> bool:
        """Evaluate whether an absence claim is legally valid under the given coverage."""
        ...

    def evaluate_facet_limitations(self, snapshot: dict[str, Any], dimension: str) -> list[str]:
        """Inspect facet declarations and extract limitation reasons."""
        ...

    def compare_observations(
        self,
        left: dict[str, Any],
        right: dict[str, Any],
        providers_differ: bool = False,
    ) -> DifferentialReport:
        """Compare two observation dossiers and emit a deterministic 3-valued DifferentialReport."""
        ...

    def export_report(self, report: DifferentialReport) -> dict[str, Any]:
        """Serialize DifferentialReport to a machine-readable JSON dictionary."""
        ...


DIFFERENTIAL_FACET_SERVICE_KEY: ServiceKey[DifferentialFacetService] = ServiceKey(
    "service.differential_facet"
)
FACET_AVAILABILITY_SERVICE_KEY: ServiceKey[DifferentialFacetService] = DIFFERENTIAL_FACET_SERVICE_KEY


def resolve_differential_facet(ctx: ServiceContext) -> DifferentialFacetService | None:
    """Resolve DifferentialFacetService from context if registered."""
    return ctx.optional(DIFFERENTIAL_FACET_SERVICE_KEY)


# -----------------------------------------------------------------------------
# Standard Implementation
# -----------------------------------------------------------------------------

class StandardDifferentialFacetService:
    """Standard in-memory implementation of DifferentialFacetService."""

    def validate_absence_claim(self, coverage: CoverageDeclaration) -> bool:
        return coverage.absence_claimable

    def evaluate_facet_limitations(self, snapshot: dict[str, Any], dimension: str) -> list[str]:
        facet_map = snapshot.get("facet_availability") or {}
        dim_facet = facet_map.get(dimension)

        if isinstance(dim_facet, dict):
            is_avail = dim_facet.get("available", True)
            reason = dim_facet.get("reason")
            if not is_avail:
                return [f"{dimension}: {reason or 'Facet marked unavailable'}" ]
        elif isinstance(dim_facet, FacetAvailability):
            if not dim_facet.available:
                return [f"{dimension}: {dim_facet.reason or 'Facet marked unavailable'}"]

        # Check undeclared empty facet
        items = snapshot.get(dimension)
        count = len(items) if isinstance(items, (list, dict, set)) else 0
        if dim_facet is None and count == 0 and "coverage" not in snapshot:
            return [f"{dimension}: Provider did not declare coverage for this empty facet."]

        return []

    def _normalize_facet(self, val: Any) -> tuple[FacetAvailability | None, int | None, str | None]:
        """Return (availability, count, digest) for a given dimension entry in a snapshot."""
        if val is None:
            return None, None, None

        if isinstance(val, list):
            count = len(val)
            digest = compute_canonical_hash(canonicalize_json(val))
            return FacetAvailability(available=True), count, digest

        if isinstance(val, dict):
            # Could be a direct facet object or structured dimension
            if "available" in val:
                avail = val.get("available", True)
                reason = val.get("reason")
                if not avail and not reason:
                    reason = "Unspecified facet omission"
                fa = FacetAvailability(available=avail, reason=reason)
                items = val.get("items") or val.get("content")
                if items is not None and isinstance(items, list):
                    count = len(items)
                    digest = compute_canonical_hash(canonicalize_json(items))
                else:
                    count = val.get("count")
                    digest = val.get("digest")
                return fa, count, digest
            else:
                count = len(val)
                digest = compute_canonical_hash(canonicalize_json(val))
                return FacetAvailability(available=True), count, digest

        # String or primitive representation
        s_val = str(val)
        return FacetAvailability(available=True), 1, compute_canonical_hash(s_val)

    def compare_observations(
        self,
        left: dict[str, Any],
        right: dict[str, Any],
        providers_differ: bool = False,
    ) -> DifferentialReport:
        left_id = left.get("id") or left.get("evidence_id") or f"ev:{compute_canonical_hash(canonicalize_json(left))}"
        right_id = right.get("id") or right.get("evidence_id") or f"ev:{compute_canonical_hash(canonicalize_json(right))}"

        # If providers differ flag not explicitly passed, inspect provider declarations
        if not providers_differ:
            left_prov = left.get("provider") or left.get("provider_id")
            right_prov = right.get("provider") or right.get("provider_id")
            if left_prov and right_prov and left_prov != right_prov:
                providers_differ = True

        # Collect target dimensions
        target_dims: list[str] = []
        for dim in sorted(VALID_DIMENSIONS):
            if (
                dim in left
                or dim in right
                or (left.get("facet_availability") and dim in left["facet_availability"])
                or (right.get("facet_availability") and dim in right["facet_availability"])
            ):
                target_dims.append(dim)

        if not target_dims:
            # Default to standard comparable dimensions if none explicitly present
            target_dims = ["identity", "pseudocode", "assembly"]

        outcomes: list[DimensionOutcome] = []
        report_limitations: list[str] = []

        if providers_differ:
            report_limitations.append("providersDiffer: Observations generated by differing providers; raw syntax decoupled.")

        for dim in target_dims:
            left_limits = self.evaluate_facet_limitations(left, dim)
            right_limits = self.evaluate_facet_limitations(right, dim)
            combined_limits = list(dict.fromkeys(left_limits + right_limits))

            l_fa, l_count, l_digest = self._normalize_facet(left.get(dim))
            r_fa, r_count, r_digest = self._normalize_facet(right.get(dim))

            # Also check facet_availability map overrides
            l_map = (left.get("facet_availability") or {}).get(dim)
            if l_map:
                if isinstance(l_map, dict) and not l_map.get("available", True):
                    l_fa = FacetAvailability(available=False, reason=l_map.get("reason") or "Facet marked unavailable")
                elif isinstance(l_map, FacetAvailability) and not l_map.available:
                    l_fa = l_map

            r_map = (right.get("facet_availability") or {}).get(dim)
            if r_map:
                if isinstance(r_map, dict) and not r_map.get("available", True):
                    r_fa = FacetAvailability(available=False, reason=r_map.get("reason") or "Facet marked unavailable")
                elif isinstance(r_map, FacetAvailability) and not r_map.available:
                    r_fa = r_map

            # Check if either side is unavailable or undeclared empty
            is_unknown = False
            if l_fa and not l_fa.available:
                is_unknown = True
            elif r_fa and not r_fa.available:
                is_unknown = True
            elif left_limits or right_limits:
                is_unknown = True

            if is_unknown:
                outcomes.append(
                    DimensionOutcome(
                        dimension=dim,
                        status="unknown",
                        conclusion_kind="unresolved",
                        left_digest=None,
                        right_digest=None,
                        left_count=None,
                        right_count=None,
                        limitations=tuple(combined_limits),
                    )
                )
                continue

            # Both facets are available
            if l_digest == r_digest and l_count == r_count:
                outcomes.append(
                    DimensionOutcome(
                        dimension=dim,
                        status="unchanged",
                        conclusion_kind="derived_relationship",
                        left_digest=l_digest,
                        right_digest=r_digest,
                        left_count=l_count,
                        right_count=r_count,
                        limitations=tuple(combined_limits),
                    )
                )
            else:
                # Digests or counts differ
                dim_limits = list(combined_limits)
                if providers_differ and dim in {"assembly", "pseudocode"}:
                    dim_limits.append(f"{dim}: providersDiffer - isolated formatting syntax disparity.")
                    conclusion_kind = "contradiction"
                else:
                    conclusion_kind = "contradiction" if providers_differ else "derived_relationship"

                outcomes.append(
                    DimensionOutcome(
                        dimension=dim,
                        status="changed",
                        conclusion_kind=conclusion_kind,
                        left_digest=l_digest,
                        right_digest=r_digest,
                        left_count=l_count,
                        right_count=r_count,
                        limitations=tuple(dim_limits),
                    )
                )

        # Aggregate overall status
        statuses = {d.status for d in outcomes}
        if "unknown" in statuses:
            overall_status = "unknown"
        elif "changed" in statuses:
            overall_status = "changed"
        else:
            overall_status = "unchanged"

        # Compute summary digest
        serialized_dimensions = [
            {
                "dimension": d.dimension,
                "status": d.status,
                "conclusion_kind": d.conclusion_kind,
                "left_digest": d.left_digest,
                "right_digest": d.right_digest,
                "left_count": d.left_count,
                "right_count": d.right_count,
                "limitations": list(d.limitations),
            }
            for d in outcomes
        ]
        summary_digest = compute_canonical_hash(canonicalize_json(serialized_dimensions))
        report_id = f"rep:{summary_digest}"

        return DifferentialReport(
            report_id=report_id,
            overall_status=overall_status,
            left_evidence_id=left_id,
            right_evidence_id=right_id,
            dimensions=tuple(outcomes),
            summary_digest=summary_digest,
            limitations=tuple(report_limitations),
        )

    def export_report(self, report: DifferentialReport) -> dict[str, Any]:
        return {
            "version": "1.0.0",
            "report_id": report.report_id,
            "overall_status": report.overall_status,
            "summary_digest": report.summary_digest,
            "evidence": {
                "left": report.left_evidence_id,
                "right": report.right_evidence_id,
            },
            "dimensions": [
                {
                    "dimension": d.dimension,
                    "status": d.status,
                    "conclusion_kind": d.conclusion_kind,
                    "left_digest": d.left_digest,
                    "right_digest": d.right_digest,
                    "left_count": d.left_count,
                    "right_count": d.right_count,
                    "limitations": list(d.limitations),
                    "evidence_links": list(d.evidence_links),
                }
                for d in report.dimensions
            ],
            "limitations": list(report.limitations),
        }
