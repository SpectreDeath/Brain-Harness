"""TrustGraph Ontology Governor Plugin — IoC provider and sandboxed entrypoints."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import sys
from typing import Any

import structlog

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_HARNESS_SRC = _REPO_ROOT / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext, ServiceKey  # noqa: E402
from harness.plugins.base import HarnessPlugin  # noqa: E402
from harness.services.trustgraph_governor import (  # noqa: E402
    DEFAULT_BYPASS_SELECTOR_BELOW,
    DEFAULT_SELECTOR_SIMILARITY_THRESHOLD,
    DEFAULT_SELECTOR_TOP_K,
    TRUSTGRAPH_GOVERNOR_KEY,
    LayaDecisionScoreReport,
    OntologyValidationReport,
    ProvenanceTraceEnvelope,
    ShaclPolicyFilterReport,
    TrustGraphGovernorProtocol,
)

try:
    from .service import DefaultTrustGraphGovernorService
except ImportError:
    from service import DefaultTrustGraphGovernorService  # type: ignore[no-redef]

logger = structlog.get_logger(__name__)


class TrustGraphOntologyGovernorPlugin(HarnessPlugin, TrustGraphGovernorProtocol):
    """HarnessPlugin providing TrustGraphGovernorProtocol in the IoC container (Rule 45)."""

    name = "plugin.trustgraph_ontology_governor"
    version = "1.0.0"
    description = (
        "TrustGraph SHACL-AF PolicyFilter, OntologyRAG small-schema bypass & subclass validator, "
        "PROV-O dual named-graph explainability, and Laya entropy decision scorer"
    )
    trusted = True

    def __init__(self) -> None:
        super().__init__()
        self._service = DefaultTrustGraphGovernorService(root_dir=_REPO_ROOT)

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [TRUSTGRAPH_GOVERNOR_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(TRUSTGRAPH_GOVERNOR_KEY, self, provider=self.name)
        logger.info("TrustGraphOntologyGovernorPlugin registered into IoC container")

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    def evaluate_shacl_policy_filter(
        self,
        triples: list[dict[str, str]] | tuple[dict[str, str], ...],
        policies: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        subject_attributes: dict[str, dict[str, Any]] | None = None,
    ) -> ShaclPolicyFilterReport:
        return self._service.evaluate_shacl_policy_filter(
            triples=triples,
            policies=policies,
            subject_attributes=subject_attributes,
        )

    def validate_ontology_extractions(
        self,
        ontology: dict[str, Any],
        triples: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        bypass_selector_below: int = DEFAULT_BYPASS_SELECTOR_BELOW,
        top_k: int = DEFAULT_SELECTOR_TOP_K,
        similarity_threshold: float = DEFAULT_SELECTOR_SIMILARITY_THRESHOLD,
    ) -> OntologyValidationReport:
        return self._service.validate_ontology_extractions(
            ontology=ontology,
            triples=triples,
            bypass_selector_below=bypass_selector_below,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

    def build_provenance_trace(
        self,
        question_id: str,
        query_text: str,
        document_id: str | None = None,
        extraction_triples: list[dict[str, str]] | tuple[dict[str, str], ...] = (),
        stage_details: dict[str, str] | None = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int | None = None,
    ) -> ProvenanceTraceEnvelope:
        return self._service.build_provenance_trace(
            question_id=question_id,
            query_text=query_text,
            document_id=document_id,
            extraction_triples=extraction_triples,
            stage_details=stage_details,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    def score_laya_decision(
        self,
        question_type: str,
        options: list[str] | tuple[str, ...],
        logits_or_probs: list[float] | tuple[float, ...],
        temperature: float = 1.0,
        question_tokens: int = 32,
        option_tokens_each: int = 12,
        probs_already_normalized: bool = False,
        temp_buckets: int = 10,
    ) -> LayaDecisionScoreReport:
        return self._service.score_laya_decision(
            question_type=question_type,
            options=options,
            logits_or_probs=logits_or_probs,
            temperature=temperature,
            question_tokens=question_tokens,
            option_tokens_each=option_tokens_each,
            probs_already_normalized=probs_already_normalized,
            temp_buckets=temp_buckets,
        )


plugin = TrustGraphOntologyGovernorPlugin()


def tg_evaluate_shacl_policy(
    triples: list[dict[str, str]],
    policies: list[dict[str, Any]] | None = None,
    subject_attributes: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate SHACL-AF subject-IRI policies over triple dictionaries."""
    return asdict(
        plugin.evaluate_shacl_policy_filter(
            triples=triples,
            policies=policies or (),
            subject_attributes=subject_attributes,
        )
    )


def tg_validate_ontology_triples(
    ontology: dict[str, Any],
    triples: list[dict[str, Any]],
    bypass_selector_below: int = DEFAULT_BYPASS_SELECTOR_BELOW,
    top_k: int = DEFAULT_SELECTOR_TOP_K,
    similarity_threshold: float = DEFAULT_SELECTOR_SIMILARITY_THRESHOLD,
) -> dict[str, Any]:
    """Validate extracted triples against OntologyRAG schemas with cycle-safe closure."""
    return asdict(
        plugin.validate_ontology_extractions(
            ontology=ontology,
            triples=triples,
            bypass_selector_below=bypass_selector_below,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )
    )


def tg_build_provenance_trace(
    question_id: str,
    query_text: str,
    document_id: str | None = None,
    extraction_triples: list[dict[str, str]] | None = None,
    stage_details: dict[str, str] | None = None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int | None = None,
) -> dict[str, Any]:
    """Build dual named-graph PROV-O extraction & 5-stage explainability traces."""
    return asdict(
        plugin.build_provenance_trace(
            question_id=question_id,
            query_text=query_text,
            document_id=document_id,
            extraction_triples=extraction_triples or (),
            stage_details=stage_details,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
    )


def tg_score_laya_decision(
    question_type: str,
    options: list[str],
    logits_or_probs: list[float],
    temperature: float = 1.0,
    question_tokens: int = 32,
    option_tokens_each: int = 12,
    probs_already_normalized: bool = False,
    temp_buckets: int = 10,
) -> dict[str, Any]:
    """Score Laya ONNX routing decisions with temperature clamping & entropy confidence."""
    return asdict(
        plugin.score_laya_decision(
            question_type=question_type,
            options=options,
            logits_or_probs=logits_or_probs,
            temperature=temperature,
            question_tokens=question_tokens,
            option_tokens_each=option_tokens_each,
            probs_already_normalized=probs_already_normalized,
            temp_buckets=temp_buckets,
        )
    )
