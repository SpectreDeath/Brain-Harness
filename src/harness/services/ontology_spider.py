"""Micro-kernel Ontology-Spider service (Rule 49) with entropy & epistemic auditing."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Union, runtime_checkable

from harness.kernel.context import ServiceKey

try:
    from ontology_spider.api import (
        evaluate_competency_questions,
        export_model,
        rank_discriminating_attributes,
        run_query,
        validate_model,
    )

    HAS_ONTOLOGY_SPIDER = True
except ModuleNotFoundError:
    HAS_ONTOLOGY_SPIDER = False
    evaluate_competency_questions = None  # type: ignore[assignment]
    export_model = None  # type: ignore[assignment]
    rank_discriminating_attributes = None  # type: ignore[assignment]
    run_query = None  # type: ignore[assignment]
    validate_model = None  # type: ignore[assignment]


@dataclass(slots=True, frozen=True)
class AttributeEntropyRank:
    """Slotted immutable value object ranking an entity attribute by information gain."""

    attribute: str
    entropy_bits: float
    coverage: float
    distinct_values: int
    laya_score: float

    def __post_init__(self) -> None:
        if (
            self.entropy_bits < 0.0
            or not (0.0 <= self.coverage <= 1.0)
            or self.distinct_values < 0
            or self.laya_score < 0.0
        ):
            raise ValueError("AttributeEntropyRank metrics out of valid range")


@dataclass(slots=True, frozen=True)
class CompetencyScorecardReport:
    """Slotted immutable Gruber 5-criteria competency question scorecard."""

    vault_uri: str
    total_questions: int
    answered_questions: int
    violation_count: int
    clarity: float
    coherence: float
    extendibility: float
    minimal_encoding_bias: float
    minimal_commitment: float
    overall_score: float
    question_results: tuple[dict[str, Any], ...]

    def __post_init__(self) -> None:
        if self.total_questions < 0 or self.answered_questions < 0 or self.violation_count < 0:
            raise ValueError("CompetencyScorecardReport counts must be non-negative")
        if not (0.0 <= self.overall_score <= 1.0):
            raise ValueError("CompetencyScorecardReport.overall_score must be in [0.0, 1.0]")


@dataclass(slots=True, frozen=True)
class EpistemicVaultAuditReport:
    """Slotted immutable federated epistemic audit over a Knowledge Vault."""

    vault_uri: str
    entities_count: int
    assertions_count: int
    structural_violations: tuple[dict[str, Any], ...]
    unverified_entity_ids: tuple[str, ...]
    top_discriminating_attributes: tuple[AttributeEntropyRank, ...]
    gruber_coherence: float
    status: str

    def __post_init__(self) -> None:
        if self.entities_count < 0 or self.assertions_count < 0:
            raise ValueError("EpistemicVaultAuditReport counts must be non-negative")
        if self.status not in ("verified", "violations_detected"):
            raise ValueError("EpistemicVaultAuditReport.status must be 'verified' or 'violations_detected'")


@runtime_checkable
class OntologySpiderProtocol(Protocol):
    """Typed micro-kernel contract for ontological vault loading, querying, and auditing."""

    def load_vault(
        self, vault_source: Union[str, Path, dict[str, Any]], *, as_of: str | None = None, min_confidence: float = 0.0
    ) -> Any: ...
    def query(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        query_str: str,
        *,
        rank_by_distance: bool = False,
        as_of: str | None = None,
        min_confidence: float = 0.0,
    ) -> dict[str, Any]: ...
    def validate(
        self, vault_source: Union[str, Path, dict[str, Any]], *, as_of: str | None = None, min_confidence: float = 0.0
    ) -> list[dict[str, Any]]: ...
    def export(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        format: str = "json",
        *,
        as_of: str | None = None,
        min_confidence: float = 0.0,
    ) -> str: ...
    def rank_attributes(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        candidate_ids: Sequence[str] | None = None,
        *,
        as_of: str | None = None,
    ) -> tuple[AttributeEntropyRank, ...]: ...
    def evaluate_competency(
        self, vault_source: Union[str, Path, dict[str, Any]], questions: Sequence[str], *, as_of: str | None = None
    ) -> CompetencyScorecardReport: ...
    def audit_vault_epistemics(
        self, vault_source: Union[str, Path, dict[str, Any]], *, as_of: str | None = None, min_confidence: float = 0.0
    ) -> EpistemicVaultAuditReport: ...


ONTOLOGY_SPIDER_SERVICE_KEY: ServiceKey[OntologySpiderProtocol] = ServiceKey("memory.ontology_spider_service")


def _require_engine() -> None:
    if not HAS_ONTOLOGY_SPIDER:
        raise RuntimeError(
            "Ontology-Spider engine is not installed. Run: pip install -e <path-to-Ontology-Spider> "
            "(see plugins/memory_and_epistemics/ontology_spider/README.md)."
        )


def _to_entropy_ranks(raw_ranks: Sequence[dict[str, Any]]) -> tuple[AttributeEntropyRank, ...]:
    return tuple(
        AttributeEntropyRank(
            attribute=str(item["attribute"]),
            entropy_bits=float(item["entropy_bits"]),
            coverage=float(item["coverage"]),
            distinct_values=int(item["distinct_values"]),
            laya_score=float(item["laya_score"]),
        )
        for item in raw_ranks
    )


class OntologySpiderKernelService(OntologySpiderProtocol):
    """In-memory micro-kernel service backed by Ontology-Spider and HarnessVaultModelSource."""

    def load_vault(
        self, vault_source: Union[str, Path, dict[str, Any]], *, as_of: str | None = None, min_confidence: float = 0.0
    ) -> Any:
        _require_engine()
        from plugins.memory_and_epistemics.ontology_spider.adapter import HarnessVaultModelSource

        return HarnessVaultModelSource(vault_source, as_of=as_of, min_confidence=min_confidence).load()

    def query(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        query_str: str,
        *,
        rank_by_distance: bool = False,
        as_of: str | None = None,
        min_confidence: float = 0.0,
    ) -> dict[str, Any]:
        model = self.load_vault(vault_source, as_of=as_of, min_confidence=min_confidence)
        raw = run_query(model, query_str).to_dict()
        if not rank_by_distance:
            return raw
        reranked: list[dict[str, Any]] = []
        for ans in raw.get("answers") or []:
            item = dict(ans)
            hop = max(0, len(item.get("path") or []) - 1)
            item["hop_distance"] = hop
            item["distance_score"] = round(1.0 / (1.0 + hop), 4)
            reranked.append(item)
        reranked.sort(key=lambda entry: (int(entry["hop_distance"]), str(entry.get("value", ""))))
        raw["answers"] = reranked
        return raw

    def validate(
        self, vault_source: Union[str, Path, dict[str, Any]], *, as_of: str | None = None, min_confidence: float = 0.0
    ) -> list[dict[str, Any]]:
        return validate_model(self.load_vault(vault_source, as_of=as_of, min_confidence=min_confidence))

    def export(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        format: str = "json",
        *,
        as_of: str | None = None,
        min_confidence: float = 0.0,
    ) -> str:
        return export_model(self.load_vault(vault_source, as_of=as_of, min_confidence=min_confidence), format=format)

    def rank_attributes(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        candidate_ids: Sequence[str] | None = None,
        *,
        as_of: str | None = None,
    ) -> tuple[AttributeEntropyRank, ...]:
        return _to_entropy_ranks(
            rank_discriminating_attributes(self.load_vault(vault_source, as_of=as_of), candidate_ids)
        )

    def evaluate_competency(
        self, vault_source: Union[str, Path, dict[str, Any]], questions: Sequence[str], *, as_of: str | None = None
    ) -> CompetencyScorecardReport:
        data = evaluate_competency_questions(self.load_vault(vault_source, as_of=as_of), questions)
        return CompetencyScorecardReport(
            vault_uri=str(data["uri"]),
            total_questions=int(data["total_questions"]),
            answered_questions=int(data["answered_questions"]),
            violation_count=int(data["violation_count"]),
            clarity=float(data["clarity"]),
            coherence=float(data["coherence"]),
            extendibility=float(data["extendibility"]),
            minimal_encoding_bias=float(data["minimal_encoding_bias"]),
            minimal_commitment=float(data["minimal_commitment"]),
            overall_score=float(data["overall_score"]),
            question_results=tuple(data["question_results"]),
        )

    def audit_vault_epistemics(
        self, vault_source: Union[str, Path, dict[str, Any]], *, as_of: str | None = None, min_confidence: float = 0.0
    ) -> EpistemicVaultAuditReport:
        model = self.load_vault(vault_source, as_of=as_of, min_confidence=min_confidence)
        violations = tuple(validate_model(model))
        unverified = tuple(
            sorted(eid for eid, ent in model.entities.items() if ent.attributes.get("isnad_verified") is False)
        )
        ranked = _to_entropy_ranks(rank_discriminating_attributes(model)[:5])
        coherence = 1.0 if not violations else round(max(0.0, 1.0 - 0.25 * len(violations)), 4)
        return EpistemicVaultAuditReport(
            vault_uri=model.uri,
            entities_count=len(model.entities),
            assertions_count=len(model.assertions),
            structural_violations=violations,
            unverified_entity_ids=unverified,
            top_discriminating_attributes=ranked,
            gruber_coherence=coherence,
            status="violations_detected" if violations else "verified",
        )
