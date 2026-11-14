"""Subprocess-isolated service adapter for TrustGraph Ontology Governor."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
from typing import Any

from harness.services.trustgraph_governor import (
    DEFAULT_BYPASS_SELECTOR_BELOW,
    DEFAULT_SELECTOR_SIMILARITY_THRESHOLD,
    DEFAULT_SELECTOR_TOP_K,
    LayaDecisionScoreReport,
    OntologyValidationReport,
    ProvenanceTraceEnvelope,
    ShaclPolicyFilterReport,
    TrustGraphGovernorEngine,
    TrustGraphGovernorProtocol,
)


class DefaultTrustGraphGovernorService(TrustGraphGovernorProtocol):
    """Service adapter delegating to TrustGraphGovernorEngine with Rule 14 subprocess pipe cleanup."""

    def __init__(self, root_dir: Path | None = None) -> None:
        self._root_dir = root_dir or Path(__file__).resolve().parents[3]
        self._engine = TrustGraphGovernorEngine()

    def evaluate_shacl_policy_filter(
        self,
        triples: list[dict[str, str]] | tuple[dict[str, str], ...],
        policies: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        subject_attributes: dict[str, dict[str, Any]] | None = None,
    ) -> ShaclPolicyFilterReport:
        return self._engine.evaluate_shacl_policy_filter(
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
        return self._engine.validate_ontology_extractions(
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
        return self._engine.build_provenance_trace(
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
        return self._engine.score_laya_decision(
            question_type=question_type,
            options=options,
            logits_or_probs=logits_or_probs,
            temperature=temperature,
            question_tokens=question_tokens,
            option_tokens_each=option_tokens_each,
            probs_already_normalized=probs_already_normalized,
            temp_buckets=temp_buckets,
        )

    async def run_cli_subprocess(self, args: list[str], *, timeout: float = 30.0) -> dict[str, Any]:
        """Execute the skill CLI engine in a subprocess with explicit Rule 14 pipe closure."""
        script_path = (
            self._root_dir
            / ".agents"
            / "skills"
            / "trustgraph-ontology-governor"
            / "scripts"
            / "trustgraph_governor_engine.py"
        )
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_data, stderr_data = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "returncode": proc.returncode,
                "stdout": stdout_data.decode("utf-8", errors="replace"),
                "stderr": stderr_data.decode("utf-8", errors="replace"),
            }
        finally:
            for pipe in (proc.stdin, proc.stdout, proc.stderr):
                close_fn = getattr(pipe, "close", None)
                if callable(close_fn):
                    try:
                        close_fn()
                    except Exception:
                        pass
