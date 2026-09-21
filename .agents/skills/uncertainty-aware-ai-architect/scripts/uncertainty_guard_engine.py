"""UncertaintyGuardEngine — Slotted, frozen domain engine for deterministic AI uncertainty interception.

Implements Chidiebere Njoku's 2026 foundational framework (ki_njoku_uncertainty_aware_systems)
for 3-layer request interception:
1. Input Intent & Boundary Detection (Sim < 0.45 -> Reject)
2. Semantic Distance & Retrieval Quality Scoring (Sim < 0.60 -> Block Context & HITL Escalate)
3. Probabilistic Logit Entropy & Output Validation (Avg < -0.35 -> Trigger Calibrated Fallback)
"""

from __future__ import annotations

import collections
import datetime
import math
import re
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Slotted & Frozen Domain Models (Rule 12 & Rule 43)
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class DomainBoundaryConfig:
    """Configuration defining authorized enterprise operational domains."""

    target_domains: tuple[str, ...] = (
        "company VPN configuration",
        "employee payroll schedules",
        "internal IT software deployment",
        "benefits enrollment and health insurance",
        "enterprise single sign-on authentication",
    )
    similarity_threshold: float = 0.45

    def __post_init__(self) -> None:
        assert 0.0 <= self.similarity_threshold <= 1.0, (
            f"similarity_threshold must be in [0, 1], got {self.similarity_threshold}"
        )
        assert len(self.target_domains) > 0, (
            "target_domains must contain at least one domain"
        )


@dataclass(slots=True, frozen=True)
class BoundaryGatingResult:
    """Outcome of Layer 1 input domain boundary evaluation."""

    is_valid: bool
    score: float
    matched_domain: str
    latency_ms: float
    reason: str

    def __post_init__(self) -> None:
        assert -1.0 <= self.score <= 1.0, (
            f"score must be between -1.0 and 1.0, got {self.score}"
        )
        assert self.latency_ms >= 0.0, "latency_ms must be non-negative"


@dataclass(slots=True, frozen=True)
class RetrievalChunk:
    """Individual retrieved document chunk scored against query."""

    chunk_id: str
    content: str
    score: float

    def __post_init__(self) -> None:
        assert -1.0 <= self.score <= 1.0, (
            f"score must be between -1.0 and 1.0, got {self.score}"
        )


@dataclass(slots=True, frozen=True)
class RetrievalScoringResult:
    """Outcome of Layer 2 retrieval quality & semantic distance scoring."""

    has_sufficient_context: bool
    top_score: float
    min_threshold: float
    scored_chunks: tuple[RetrievalChunk, ...]
    action: str

    def __post_init__(self) -> None:
        assert -1.0 <= self.top_score <= 1.0, (
            f"top_score must be between -1.0 and 1.0, got {self.top_score}"
        )


@dataclass(slots=True, frozen=True)
class LogprobAuditResult:
    """Outcome of Layer 3 probabilistic logit analysis & output validation."""

    is_confident: bool
    avg_logprob: float
    perplexity: float
    threshold: float
    token_count: int
    action: str

    def __post_init__(self) -> None:
        assert self.token_count >= 0, "token_count must be non-negative"
        assert self.perplexity >= 0.0, "perplexity must be non-negative"


@dataclass(slots=True, frozen=True)
class HitlEscalationTicket:
    """Payload representing an intentional escalation to Human-In-The-Loop queues."""

    ticket_id: str
    timestamp: str
    query: str
    failure_gate: str
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        assert len(self.ticket_id) > 0, "ticket_id cannot be empty"
        assert self.failure_gate in (
            "BOUNDARY_GATE",
            "RETRIEVAL_GATE",
            "LOGPROB_GATE",
            "MANUAL",
        ), f"Invalid failure_gate: {self.failure_gate}"


@dataclass(slots=True, frozen=True)
class DocDebtCluster:
    """Clustered documentation debt mined from repeated low-relevance retrievals."""

    cluster_id: str
    representative_topic: str
    query_count: int
    sample_queries: tuple[str, ...]
    severity: str

    def __post_init__(self) -> None:
        assert self.query_count >= 1, "query_count must be at least 1"
        assert self.severity in (
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        ), f"Invalid severity: {self.severity}"


@dataclass(slots=True, frozen=True)
class PipelineInterceptionResult:
    """Unified outcome of the end-to-end 3-layer request interception lifecycle."""

    state: str  # "PASSED_VERIFIED", "REJECTED_OUT_OF_DOMAIN", "ESCALATED_LOW_CONTEXT", "FALLBACK_UNCERTAIN_LOGPROBS"
    gate_passed: int  # 0 to 3
    total_latency_ms: float
    boundary_result: BoundaryGatingResult
    retrieval_result: RetrievalScoringResult | None
    logprob_result: LogprobAuditResult | None
    escalation_ticket: HitlEscalationTicket | None
    response_text: str

    def __post_init__(self) -> None:
        assert self.state in (
            "PASSED_VERIFIED",
            "REJECTED_OUT_OF_DOMAIN",
            "ESCALATED_LOW_CONTEXT",
            "FALLBACK_UNCERTAIN_LOGPROBS",
        ), f"Invalid pipeline state: {self.state}"
        assert 0 <= self.gate_passed <= 3, "gate_passed must be between 0 and 3"
        assert self.total_latency_ms >= 0.0, "total_latency_ms must be non-negative"


# ---------------------------------------------------------------------------
# Zero-Dependency Semantic Matcher (Sub-Millisecond Execution)
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "because",
    "as",
    "what",
    "which",
    "this",
    "that",
    "these",
    "those",
    "then",
    "just",
    "so",
    "than",
    "such",
    "both",
    "through",
    "about",
    "for",
    "is",
    "of",
    "while",
    "during",
    "to",
    "from",
    "in",
    "out",
    "on",
    "off",
    "again",
    "further",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "any",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "too",
    "very",
    "can",
    "will",
    "should",
    "now",
    "i",
    "me",
    "my",
    "we",
    "our",
    "you",
    "your",
    "he",
    "him",
    "his",
    "she",
    "her",
    "it",
    "its",
    "they",
    "them",
    "their",
    "do",
    "did",
}

_SYNONYMS = {
    "corporate": "company",
    "enterprise": "company",
    "org": "company",
    "business": "company",
    "firm": "company",
    "setup": "configure",
    "settings": "configure",
    "config": "configure",
    "configuration": "configure",
    "configuring": "configure",
    "install": "deploy",
    "installation": "deploy",
    "deployment": "deploy",
    "deploying": "deploy",
    "client": "software",
    "tool": "software",
    "application": "software",
    "app": "software",
    "login": "auth",
    "signin": "auth",
    "authentication": "auth",
    "sso": "auth",
    "salary": "payroll",
    "wages": "payroll",
    "paycheck": "payroll",
    "compensation": "payroll",
    "insurance": "benefits",
    "healthcare": "benefits",
    "guide": "guidelines",
    "manual": "guidelines",
    "documentation": "guidelines",
    "instructions": "guidelines",
}


def _stem(w: str) -> str:
    for s in [
        "ation",
        "tions",
        "tion",
        "ment",
        "ments",
        "ing",
        "ers",
        "er",
        "es",
        "ed",
        "s",
    ]:
        if len(w) > len(s) + 3 and w.endswith(s):
            return w[: -len(s)]
    return w


def _normalize_token(w: str) -> str | None:
    w_clean = re.sub(r"[^\w]", "", w.lower())
    if not w_clean or w_clean in _STOPWORDS:
        return None
    canon = _SYNONYMS.get(w_clean, w_clean)
    return _stem(canon)


def _get_tokens(text: str) -> list[str]:
    words = re.findall(r"\w+", text.lower())
    tokens: list[str] = []
    for w in words:
        norm = _normalize_token(w)
        if norm:
            tokens.append(norm)
    return tokens


class ZeroDepSemanticMatcher:
    """High-speed character n-gram & token frequency vectorizer for sub-millisecond cosine evaluation."""

    __slots__ = ("_vocab_dim",)

    def __init__(self, vocab_dim: int = 4096) -> None:
        self._vocab_dim = vocab_dim

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode a batch of text strings into normalized L2 dense feature vectors."""
        if not texts:
            return np.zeros((0, self._vocab_dim), dtype=np.float32)

        matrix = np.zeros((len(texts), self._vocab_dim), dtype=np.float32)
        for idx, text in enumerate(texts):
            tokens = _get_tokens(text)
            if not tokens:
                continue
            for tok in tokens:
                bucket = (hash(tok) ^ (hash(tok) >> 16)) % self._vocab_dim
                matrix[idx, bucket] += 1.0
            if len(tokens) >= 2:
                for i in range(len(tokens) - 1):
                    bg = f"{tokens[i]}_{tokens[i + 1]}"
                    bucket_bg = (hash(bg) ^ (hash(bg) >> 16)) % self._vocab_dim
                    matrix[idx, bucket_bg] += 1.5

            norm = np.linalg.norm(matrix[idx])
            if norm > 1e-9:
                matrix[idx] /= norm
        return matrix

    def compute_similarities(self, q_text: str, d_texts: list[str]) -> np.ndarray:
        """Compute cosine similarity and semantic intent coverage."""
        if not d_texts:
            return np.array([], dtype=np.float32)
        q_tokens = _get_tokens(q_text)
        if not q_tokens:
            return np.zeros(len(d_texts), dtype=np.float32)

        q_vec = self.encode([q_text])[0]
        d_vecs = self.encode(d_texts)
        cos_scores = np.dot(d_vecs, q_vec)

        scores: list[float] = []
        q_set = set(q_tokens)
        for i, d in enumerate(d_texts):
            d_tokens = _get_tokens(d)
            if not d_tokens:
                scores.append(0.0)
                continue
            overlap = len(q_set & set(d_tokens))
            coverage = overlap / len(q_set) if q_set else 0.0

            cos = float(cos_scores[i])
            blended = 0.5 * cos + 0.5 * coverage
            if coverage >= 0.5:
                blended = max(blended, 0.65)
            elif coverage > 0.0:
                blended = max(blended, 0.45 * coverage + 0.3 * cos)
            scores.append(round(float(min(1.0, blended)), 4))

        return np.array(scores, dtype=np.float32)


# ---------------------------------------------------------------------------
# Authoritative Slotted Domain Engine
# ---------------------------------------------------------------------------


class UncertaintyGuardEngine:
    """Authoritative engine for 3-layer deterministic uncertainty interception & overconfidence prevention."""

    __slots__ = (
        "_default_boundary_config",
        "_default_logprob_threshold",
        "_default_retrieval_threshold",
        "_escalation_queue",
        "_matcher",
        "_query_history",
    )

    def __init__(
        self,
        default_boundary_config: DomainBoundaryConfig | None = None,
        default_retrieval_threshold: float = 0.60,
        default_logprob_threshold: float = -0.35,
    ) -> None:
        self._matcher = ZeroDepSemanticMatcher()
        self._default_boundary_config = (
            default_boundary_config or DomainBoundaryConfig()
        )
        self._default_retrieval_threshold = default_retrieval_threshold
        self._default_logprob_threshold = default_logprob_threshold
        self._escalation_queue: list[HitlEscalationTicket] = []
        self._query_history: list[dict[str, Any]] = []

    # -----------------------------------------------------------------------
    # Layer 1: Input Domain & Boundary Formulation
    # -----------------------------------------------------------------------

    def verify_boundary(
        self,
        query: str,
        target_domains: list[str] | tuple[str, ...] | None = None,
        threshold: float | None = None,
    ) -> BoundaryGatingResult:
        """Evaluate incoming query against authorized operational domain centroids (default tau = 0.45)."""
        start = time.perf_counter()
        domains = tuple(target_domains or self._default_boundary_config.target_domains)
        t_val = (
            threshold
            if threshold is not None
            else self._default_boundary_config.similarity_threshold
        )

        if not query.strip():
            latency = (time.perf_counter() - start) * 1000.0
            return BoundaryGatingResult(
                is_valid=False,
                score=0.0,
                matched_domain="",
                latency_ms=round(latency, 3),
                reason="Query is empty or whitespace only",
            )

        similarities = self._matcher.compute_similarities(query, list(domains))
        if len(similarities) == 0:
            best_score = 0.0
            matched_domain = ""
        else:
            best_idx = int(np.argmax(similarities))
            best_score = float(similarities[best_idx])
            matched_domain = domains[best_idx]

        is_valid = best_score >= t_val
        latency = (time.perf_counter() - start) * 1000.0

        reason = (
            f"Within operational domain (aligns with '{matched_domain}', score={best_score:.4f} >= {t_val})"
            if is_valid
            else f"Query falls outside operational domain boundaries (max alignment={best_score:.4f} < {t_val})"
        )

        return BoundaryGatingResult(
            is_valid=is_valid,
            score=round(best_score, 4),
            matched_domain=matched_domain if is_valid else "",
            latency_ms=round(latency, 3),
            reason=reason,
        )

    # -----------------------------------------------------------------------
    # Layer 2: Retrieval Quality & Semantic Distance Scoring
    # -----------------------------------------------------------------------

    def score_retrieval(
        self,
        user_query: str,
        retrieved_chunks: list[str] | list[dict[str, str]],
        minimum_relevance: float | None = None,
    ) -> RetrievalScoringResult:
        """Compute pairwise cosine similarities between query and retrieved chunks (default tau = 0.60)."""
        min_rel = (
            minimum_relevance
            if minimum_relevance is not None
            else self._default_retrieval_threshold
        )

        if not retrieved_chunks:
            return RetrievalScoringResult(
                has_sufficient_context=False,
                top_score=0.0,
                min_threshold=min_rel,
                scored_chunks=(),
                action="BLOCK_CONTEXT_AND_ESCALATE",
            )

        chunk_texts: list[str] = []
        chunk_ids: list[str] = []
        for idx, item in enumerate(retrieved_chunks):
            if isinstance(item, dict):
                chunk_texts.append(item.get("content", item.get("text", "")))
                chunk_ids.append(item.get("id", f"chunk_{idx}"))
            else:
                chunk_texts.append(str(item))
                chunk_ids.append(f"chunk_{idx}")

        scores = self._matcher.compute_similarities(user_query, chunk_texts)

        scored_list: list[RetrievalChunk] = []
        for idx, s in enumerate(scores):
            scored_list.append(
                RetrievalChunk(
                    chunk_id=chunk_ids[idx],
                    content=chunk_texts[idx],
                    score=round(float(s), 4),
                )
            )

        scored_list.sort(key=lambda c: c.score, reverse=True)
        top_score = scored_list[0].score if scored_list else 0.0
        has_sufficient = top_score >= min_rel
        action = "INJECT_CONTEXT" if has_sufficient else "BLOCK_CONTEXT_AND_ESCALATE"

        return RetrievalScoringResult(
            has_sufficient_context=has_sufficient,
            top_score=top_score,
            min_threshold=min_rel,
            scored_chunks=tuple(scored_list),
            action=action,
        )

    # -----------------------------------------------------------------------
    # Layer 3: Probabilistic Logit Analysis & Output Validation
    # -----------------------------------------------------------------------

    def validate_logprobs(
        self,
        token_logprobs: list[float],
        logprob_threshold: float | None = None,
    ) -> LogprobAuditResult:
        """Calculate sequence mean logprob and perplexity from API payloads (default tau = -0.35)."""
        tau = (
            logprob_threshold
            if logprob_threshold is not None
            else self._default_logprob_threshold
        )

        if not token_logprobs:
            return LogprobAuditResult(
                is_confident=False,
                avg_logprob=-999.0,
                perplexity=999.0,
                threshold=tau,
                token_count=0,
                action="ACTIVATE_CALIBRATED_FALLBACK",
            )

        avg_logprob = float(sum(token_logprobs) / len(token_logprobs))
        # Perplexity = exp(-avg_logprob)
        perplexity = float(math.exp(-avg_logprob))
        is_confident = avg_logprob >= tau
        action = "DELIVER_RESPONSE" if is_confident else "ACTIVATE_CALIBRATED_FALLBACK"

        return LogprobAuditResult(
            is_confident=is_confident,
            avg_logprob=round(avg_logprob, 4),
            perplexity=round(perplexity, 4),
            threshold=tau,
            token_count=len(token_logprobs),
            action=action,
        )

    # -----------------------------------------------------------------------
    # Layer 4: Sequential Pipeline Orchestration
    # -----------------------------------------------------------------------

    def intercept_request(
        self,
        query: str,
        target_domains: list[str] | None = None,
        retrieved_chunks: list[str] | list[dict[str, str]] | None = None,
        token_logprobs: list[float] | None = None,
        draft_response: str = "",
        escalate_on_failure: bool = True,
    ) -> PipelineInterceptionResult:
        """Execute end-to-end 3-layer request interception lifecycle with deterministic routing."""
        start = time.perf_counter()

        # Gate 1: Boundary check
        boundary_res = self.verify_boundary(query, target_domains=target_domains)
        if not boundary_res.is_valid:
            total_lat = (time.perf_counter() - start) * 1000.0
            ticket = None
            if escalate_on_failure:
                ticket = self._create_ticket(
                    query=query,
                    failure_gate="BOUNDARY_GATE",
                    reason=boundary_res.reason,
                    metadata={"score": boundary_res.score},
                )
            self._record_telemetry(query, "REJECTED_OUT_OF_DOMAIN", 0)
            return PipelineInterceptionResult(
                state="REJECTED_OUT_OF_DOMAIN",
                gate_passed=0,
                total_latency_ms=round(total_lat, 3),
                boundary_result=boundary_res,
                retrieval_result=None,
                logprob_result=None,
                escalation_ticket=ticket,
                response_text="I apologize, but this request falls outside our authorized operational domains.",
            )

        # Gate 2: Retrieval check
        chunks = retrieved_chunks or []
        retrieval_res = self.score_retrieval(query, chunks)
        if not retrieval_res.has_sufficient_context:
            total_lat = (time.perf_counter() - start) * 1000.0
            ticket = None
            if escalate_on_failure:
                ticket = self._create_ticket(
                    query=query,
                    failure_gate="RETRIEVAL_GATE",
                    reason=f"Retrieved context top score {retrieval_res.top_score:.4f} < {retrieval_res.min_threshold:.4f}",
                    metadata={"top_score": retrieval_res.top_score},
                )
            self._record_telemetry(query, "ESCALATED_LOW_CONTEXT", 1)
            return PipelineInterceptionResult(
                state="ESCALATED_LOW_CONTEXT",
                gate_passed=1,
                total_latency_ms=round(total_lat, 3),
                boundary_result=boundary_res,
                retrieval_result=retrieval_res,
                logprob_result=None,
                escalation_ticket=ticket,
                response_text="I do not have sufficient documentation to answer this question accurately. This request has been escalated to human support.",
            )

        # Gate 3: Output Logprob check
        lprobs = token_logprobs or []
        logprob_res = self.validate_logprobs(lprobs)
        if not logprob_res.is_confident:
            total_lat = (time.perf_counter() - start) * 1000.0
            ticket = None
            if escalate_on_failure:
                ticket = self._create_ticket(
                    query=query,
                    failure_gate="LOGPROB_GATE",
                    reason=f"Output average logprob {logprob_res.avg_logprob:.4f} < {logprob_res.threshold:.4f} (perplexity={logprob_res.perplexity:.2f})",
                    metadata={
                        "avg_logprob": logprob_res.avg_logprob,
                        "perplexity": logprob_res.perplexity,
                    },
                )
            self._record_telemetry(query, "FALLBACK_UNCERTAIN_LOGPROBS", 2)
            return PipelineInterceptionResult(
                state="FALLBACK_UNCERTAIN_LOGPROBS",
                gate_passed=2,
                total_latency_ms=round(total_lat, 3),
                boundary_result=boundary_res,
                retrieval_result=retrieval_res,
                logprob_result=logprob_res,
                escalation_ticket=ticket,
                response_text="While relevant documentation was identified, generation confidence was below safety thresholds. Escalating for verified review.",
            )

        total_lat = (time.perf_counter() - start) * 1000.0
        self._record_telemetry(query, "PASSED_VERIFIED", 3)
        return PipelineInterceptionResult(
            state="PASSED_VERIFIED",
            gate_passed=3,
            total_latency_ms=round(total_lat, 3),
            boundary_result=boundary_res,
            retrieval_result=retrieval_res,
            logprob_result=logprob_res,
            escalation_ticket=None,
            response_text=draft_response
            or "Response verified across all 3 uncertainty boundary layers.",
        )

    # -----------------------------------------------------------------------
    # Layer 5: Continuous Calibration & Documentation Gap Mining
    # -----------------------------------------------------------------------

    def _create_ticket(
        self,
        query: str,
        failure_gate: str,
        reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> HitlEscalationTicket:
        ticket = HitlEscalationTicket(
            ticket_id=f"HITL-{uuid.uuid4().hex[:8].upper()}",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            query=query,
            failure_gate=failure_gate,
            reason=reason,
            metadata=metadata or {},
        )
        self._escalation_queue.append(ticket)
        return ticket

    def _record_telemetry(self, query: str, state: str, gate_passed: int) -> None:
        self._query_history.append(
            {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "query": query,
                "state": state,
                "gate_passed": gate_passed,
            }
        )

    def get_escalation_queue(self) -> list[HitlEscalationTicket]:
        """Return list of active HITL escalation tickets."""
        return list(self._escalation_queue)

    def mine_documentation_debt(
        self, failed_queries: list[str] | None = None
    ) -> list[DocDebtCluster]:
        """Cluster under-retrieved queries to uncover missing, outdated, or poorly indexed documentation."""
        queries = (
            failed_queries
            if failed_queries is not None
            else [
                item["query"]
                for item in self._query_history
                if item["state"] == "ESCALATED_LOW_CONTEXT"
            ]
        )

        if not queries:
            return []

        stopwords = {
            "what",
            "how",
            "is",
            "the",
            "a",
            "an",
            "for",
            "to",
            "in",
            "of",
            "and",
            "my",
            "i",
            "can",
            "do",
            "where",
            "when",
            "steps",
            "instructions",
            "details",
            "setup",
        }

        # Extract content words per query and count word frequency
        query_tokens: list[list[str]] = []
        word_freq: collections.Counter[str] = collections.Counter()
        for q in queries:
            words = [
                w
                for w in re.findall(r"\w+", q.lower())
                if w not in stopwords and len(w) > 1
            ]
            query_tokens.append(words)
            for w in set(words):
                word_freq[w] += 1

        # Group queries by top frequent distinctive words
        assigned = [False] * len(queries)
        clusters: list[tuple[str, list[str]]] = []

        for top_word, count in word_freq.most_common():
            if count < 1:
                continue
            cluster_queries_list: list[str] = []
            for i, words in enumerate(query_tokens):
                if not assigned[i] and top_word in words:
                    assigned[i] = True
                    cluster_queries_list.append(queries[i])

            if cluster_queries_list:
                cluster_words: collections.Counter[str] = collections.Counter()
                for q_text in cluster_queries_list:
                    for w in re.findall(r"\w+", q_text.lower()):
                        if w not in stopwords and len(w) > 1:
                            cluster_words[w] += 1
                topic_words = [w for w, _ in cluster_words.most_common(2)]
                topic = " ".join(topic_words) if topic_words else top_word
                clusters.append((topic, cluster_queries_list))

        remaining = [queries[i] for i in range(len(queries)) if not assigned[i]]
        if remaining:
            clusters.append(("miscellaneous queries", remaining))

        result: list[DocDebtCluster] = []
        for idx, (topic, q_list) in enumerate(clusters):
            count = len(q_list)
            if count >= 5:
                sev = "CRITICAL"
            elif count >= 3:
                sev = "HIGH"
            elif count >= 2:
                sev = "MEDIUM"
            else:
                sev = "LOW"

            result.append(
                DocDebtCluster(
                    cluster_id=f"DEBT-{idx + 1:03d}",
                    representative_topic=topic,
                    query_count=count,
                    sample_queries=tuple(q_list[:5]),
                    severity=sev,
                )
            )

        result.sort(key=lambda c: c.query_count, reverse=True)
        return result

    # -----------------------------------------------------------------------
    # Visual Brief Generation (Temp HTML + Mermaid)
    # -----------------------------------------------------------------------

    def generate_visual_brief(
        self,
        pipeline_result: PipelineInterceptionResult | dict[str, Any],
        output_path: str | Path | None = None,
    ) -> Path:
        """Generate interactive HTML visual brief in %TEMP% summarizing uncertainty interception."""
        if isinstance(pipeline_result, PipelineInterceptionResult):
            res = {
                "state": pipeline_result.state,
                "gate_passed": pipeline_result.gate_passed,
                "latency_ms": pipeline_result.total_latency_ms,
                "boundary_score": pipeline_result.boundary_result.score,
                "boundary_valid": pipeline_result.boundary_result.is_valid,
                "retrieval_score": (
                    pipeline_result.retrieval_result.top_score
                    if pipeline_result.retrieval_result
                    else 0.0
                ),
                "retrieval_valid": (
                    pipeline_result.retrieval_result.has_sufficient_context
                    if pipeline_result.retrieval_result
                    else False
                ),
                "logprob_avg": (
                    pipeline_result.logprob_result.avg_logprob
                    if pipeline_result.logprob_result
                    else 0.0
                ),
                "perplexity": (
                    pipeline_result.logprob_result.perplexity
                    if pipeline_result.logprob_result
                    else 0.0
                ),
                "logprob_valid": (
                    pipeline_result.logprob_result.is_confident
                    if pipeline_result.logprob_result
                    else False
                ),
                "response_text": pipeline_result.response_text,
                "ticket_id": (
                    pipeline_result.escalation_ticket.ticket_id
                    if pipeline_result.escalation_ticket
                    else None
                ),
            }
        else:
            res = pipeline_result

        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y%m%d_%H%M%S"
        )
        if output_path is None:
            temp_dir = Path(tempfile.gettempdir())
            target_file = temp_dir / f"uncertainty-brief-{timestamp}.html"
        else:
            target_file = Path(output_path)

        state_color = "#3fb950" if res["state"] == "PASSED_VERIFIED" else "#f85149"

        html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <title>Uncertainty Interception Visual Brief</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{startOnLoad:true, theme:'dark'}});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] min-h-screen p-8">
  <div class="max-w-5xl mx-auto space-y-8">
    <header class="border-b border-[#30363d] pb-4 flex justify-between items-center">
      <div>
        <div class="text-xs uppercase font-bold text-[#58a6ff]">Uncertainty-Aware AI Pipeline</div>
        <h1 class="text-2xl font-bold text-[#f0f6fc]">Request Interception Telemetry</h1>
      </div>
      <div class="px-3 py-1 rounded-full text-xs font-bold border" style="border-color: {state_color}; color: {state_color};">
        {res["state"]}
      </div>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-[#161b22] border border-[#30363d] p-4 rounded-lg text-center">
        <div class="text-xs text-[#8b949e]">Gate Passed</div>
        <div class="text-2xl font-bold text-[#f0f6fc]">{res["gate_passed"]} / 3</div>
      </div>
      <div class="bg-[#161b22] border border-[#30363d] p-4 rounded-lg text-center">
        <div class="text-xs text-[#8b949e]">Boundary Score</div>
        <div class="text-2xl font-bold text-[#58a6ff]">{res["boundary_score"]:.4f}</div>
      </div>
      <div class="bg-[#161b22] border border-[#30363d] p-4 rounded-lg text-center">
        <div class="text-xs text-[#8b949e]">Retrieval Score</div>
        <div class="text-2xl font-bold text-[#d2a8ff]">{res["retrieval_score"]:.4f}</div>
      </div>
      <div class="bg-[#161b22] border border-[#30363d] p-4 rounded-lg text-center">
        <div class="text-xs text-[#8b949e]">Avg Logprob &amp; PPL</div>
        <div class="text-2xl font-bold text-[#7ee787]">{res["logprob_avg"]:.2f} ({res["perplexity"]:.1f})</div>
      </div>
    </div>

    <section class="bg-[#161b22] border border-[#30363d] p-6 rounded-lg space-y-4">
      <h2 class="text-lg font-bold text-[#f0f6fc]">3-Layer Interception Lifecycle DAG</h2>
      <div class="mermaid">
graph LR
    Q[User Request] --> G1{{Layer 1: Boundary Centroid}}
    G1 -->|Score &gt;= 0.45| G2{{Layer 2: Retrieval Relevance}}
    G1 -->|Score &lt; 0.45| R1[Immediate Perimeter Rejection]
    G2 -->|Score &gt;= 0.60| G3{{Layer 3: Token Logprob & PPL}}
    G2 -->|Score &lt; 0.60| R2[HITL Ticket &amp; Doc Debt]
    G3 -->|Avg &gt;= -0.35| OK[Verified Output Delivered]
    G3 -->|Avg &lt; -0.35| R3[Calibrated Safe Fallback]
      </div>
    </section>

    <section class="bg-[#161b22] border border-[#30363d] p-6 rounded-lg space-y-2">
      <div class="text-xs font-bold text-[#8b949e] uppercase">Pipeline Output Response</div>
      <p class="text-sm text-[#f0f6fc] font-mono bg-[#0d1117] p-4 rounded border border-[#30363d]">{res["response_text"]}</p>
    </section>
  </div>
</body>
</html>"""

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(html)

        return target_file
