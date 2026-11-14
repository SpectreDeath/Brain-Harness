"""TrustGraph Ontology Governor Service — SHACL-AF PolicyFilter, OntologyRAG, PROV-O & Laya scoring.

Distilled from trustgraph-ai/trustgraph @ 17e5d742:
- SHACL-AF subject-IRI PolicyFilter in urn:graph:policy (sh:order sort, first-match-wins, bounded TTL caches, open mode)
- OntologyRAG small-schema bypass (< 5 elements) and cycle-safe subClassOf domain/range triple validation
- PROV-O dual named graph isolation (urn:graph:source vs urn:graph:retrieval) with 5-stage query explainability & tokens
- Laya ONNX decision scoring across choice/score/noul with temperature clamping, normalized Shannon entropy, and head budgeting
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey

POLICY_GRAPH_URI: str = "urn:graph:policy"
SOURCE_GRAPH_URI: str = "urn:graph:source"
RETRIEVAL_GRAPH_URI: str = "urn:graph:retrieval"
EXTRACTION_PROVENANCE_PREFIX: str = "https://trustgraph.ai/"
EXPLAINABILITY_URN_PREFIX: str = "urn:trustgraph:"

DEFAULT_POLICY_ORDER: int = 99
QUERY_CACHE_TTL_SECONDS: int = 30
QUERY_CACHE_MAX_ENTRIES: int = 256
SPARQL_CACHE_MAX_ENTRIES: int = 64
NODE_CACHE_TTL_SECONDS: int = 60
NODE_CACHE_MAX_ENTRIES: int = 1024

DEFAULT_BYPASS_SELECTOR_BELOW: int = 5
DEFAULT_SELECTOR_TOP_K: int = 10
DEFAULT_SELECTOR_SIMILARITY_THRESHOLD: float = 0.3

LAYA_DEFAULT_REPO: str = "onnx-community/laya-multilingual-ONNX"
LAYA_TEMP_MIN: float = 0.5
LAYA_TEMP_MAX: float = 5.0
LAYA_MAX_SEQ_LEN: int = 512
LAYA_HEAD_MAX_LEN: int = 192
LAYA_OPTION_TOKEN_CAP: int = 48
LAYA_MIN_OPT_BUDGET: int = 16
LAYA_QUESTION_TYPES: dict[str, int] = {"choice": 0, "score": 1, "noul": 2}

EXPLAINABILITY_STAGES: tuple[str, ...] = (
    "question",
    "grounding",
    "exploration",
    "focus",
    "synthesis",
)


@dataclass(slots=True, frozen=True)
class ShaclPolicyFilterReport:
    """Immutable evaluation report for SHACL-AF subject-IRI triple policy filtering."""

    open_mode: bool
    evaluated_policies: tuple[str, ...]
    blocked_subjects: tuple[str, ...]
    allowed_triples: tuple[dict[str, str], ...]
    dropped_triples: tuple[dict[str, str], ...]
    policy_evaluations: tuple[dict[str, Any], ...]
    cache_limits: dict[str, int]
    violations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.open_mode, bool):
            raise TypeError("ShaclPolicyFilterReport.open_mode must be a bool")


@dataclass(slots=True, frozen=True)
class OntologyValidationReport:
    """Immutable OntologyRAG validation report with small-schema bypass and subclass closure."""

    total_elements: int
    selector_bypassed: bool
    bypass_threshold: int
    accepted_triples: tuple[dict[str, str], ...]
    rejected_triples: tuple[dict[str, Any], ...]
    cycles_detected: tuple[str, ...] = ()
    violations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.total_elements < 0 or self.bypass_threshold < 0:
            raise ValueError("OntologyValidationReport counts must be non-negative")


@dataclass(slots=True, frozen=True)
class ProvenanceTraceEnvelope:
    """Immutable dual-named-graph PROV-O extraction and 5-stage query explainability envelope."""

    question_id: str
    source_graph: str
    retrieval_graph: str
    question_uri: str
    stage_uris: dict[str, str]
    extraction_triples: tuple[dict[str, str], ...]
    explainability_triples: tuple[dict[str, str], ...]
    token_triples_appended: bool
    total_tokens: int
    violations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.question_id or not self.question_id.strip():
            raise ValueError("ProvenanceTraceEnvelope.question_id must be non-empty")
        if self.total_tokens < 0:
            raise ValueError("ProvenanceTraceEnvelope.total_tokens must be non-negative")


@dataclass(slots=True, frozen=True)
class LayaDecisionScoreReport:
    """Immutable Laya ONNX decision scoring calibration, entropy confidence & budget report."""

    question_type: str
    qtype_id: int
    raw_temperature: float
    clamped_temperature: float
    temp_bucket: int
    probabilities: tuple[float, ...]
    selected_index: int
    entropy: float
    confidence: float
    opt_budget: int
    head_max_len: int
    max_seq_len: int
    shrink_warning: bool
    violations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.question_type not in LAYA_QUESTION_TYPES:
            raise ValueError(f"Unsupported question_type: {self.question_type!r}")
        if not (LAYA_TEMP_MIN <= self.clamped_temperature <= LAYA_TEMP_MAX):
            raise ValueError("clamped_temperature out of [0.5, 5.0] bounds")


@runtime_checkable
class TrustGraphGovernorProtocol(Protocol):
    """Typed IoC service contract for TrustGraph policy, ontology, provenance & decision scoring."""

    def evaluate_shacl_policy_filter(
        self,
        triples: list[dict[str, str]] | tuple[dict[str, str], ...],
        policies: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        subject_attributes: dict[str, dict[str, Any]] | None = None,
    ) -> ShaclPolicyFilterReport: ...

    def validate_ontology_extractions(
        self,
        ontology: dict[str, Any],
        triples: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        bypass_selector_below: int = DEFAULT_BYPASS_SELECTOR_BELOW,
        top_k: int = DEFAULT_SELECTOR_TOP_K,
        similarity_threshold: float = DEFAULT_SELECTOR_SIMILARITY_THRESHOLD,
    ) -> OntologyValidationReport: ...

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
    ) -> ProvenanceTraceEnvelope: ...

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
    ) -> LayaDecisionScoreReport: ...


TRUSTGRAPH_GOVERNOR_KEY: ServiceKey[TrustGraphGovernorProtocol] = ServiceKey("service.trustgraph_ontology_governor")


def _clamp_temperature(temperature: float) -> float:
    """Clamp non-finite values to 1.0 and finite temperatures into [0.5, 5.0]."""
    if not math.isfinite(temperature):
        return 1.0
    return max(LAYA_TEMP_MIN, min(LAYA_TEMP_MAX, float(temperature)))


def _temp_bucket(clamped_temp: float, num_buckets: int = 10) -> int:
    """Quantize a clamped temperature in [0.5, 5.0] into an integer bucket index."""
    buckets = max(1, num_buckets)
    span = LAYA_TEMP_MAX - LAYA_TEMP_MIN
    ratio = (clamped_temp - LAYA_TEMP_MIN) / span if span > 0 else 0.0
    idx = int(ratio * buckets)
    return min(buckets - 1, max(0, idx))


def _confidence_from_probs(probs: tuple[float, ...]) -> tuple[float, float]:
    """Compute (entropy, normalized Shannon confidence 1 - H(p)/ln(k)), returning 1.0 for k < 2."""
    k = len(probs)
    if k < 2:
        return 0.0, 1.0
    entropy = -sum(p * math.log(p) for p in probs if p > 0.0)
    max_entropy = math.log(k)
    confidence = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 1.0
    return round(entropy, 6), round(max(0.0, min(1.0, confidence)), 6)


def _extract_subject(triple: dict[str, Any]) -> str:
    return str(triple.get("s") or triple.get("subject") or "")


def _policy_matches_subject(
    policy: dict[str, Any],
    subject: str,
    attrs: dict[str, Any],
) -> bool:
    """Evaluate SHACL-AF target/condition predicates against a subject IRI and its attributes."""
    matched_list = policy.get("matched_subjects") or policy.get("blocked_subjects") or []
    if subject in matched_list:
        return True

    if policy.get("match_all"):
        return True

    has_constraint = False
    target_class = policy.get("target_class")
    if target_class is not None:
        has_constraint = True
        subj_types = attrs.get("types") or attrs.get("rdf:type") or attrs.get("type")
        if isinstance(subj_types, (list, tuple, set)):
            if target_class not in subj_types:
                return False
        elif subj_types != target_class:
            return False

    predicate = policy.get("predicate")
    if predicate is not None:
        has_constraint = True
        if "equals" in policy and attrs.get(str(predicate)) != policy["equals"]:
            return False
        if "equals" not in policy and str(predicate) not in attrs:
            return False

    conditions = policy.get("conditions") or policy.get("condition")
    if isinstance(conditions, dict) and conditions:
        has_constraint = True
        for key, expected in conditions.items():
            if attrs.get(str(key)) != expected:
                return False

    return has_constraint


def _normalize_classes_map(raw_classes: Any) -> dict[str, dict[str, Any]]:
    """Normalize OntologySelector/TripleConverter class definitions to a lookup dictionary."""
    if isinstance(raw_classes, dict):
        result: dict[str, dict[str, Any]] = {}
        for key, value in raw_classes.items():
            if isinstance(value, dict):
                result[str(key)] = value
            elif isinstance(value, str):
                result[str(key)] = {"subClassOf": [value]}
            elif isinstance(value, (list, tuple)):
                result[str(key)] = {"subClassOf": list(value)}
            else:
                result[str(key)] = {}
        return result
    if isinstance(raw_classes, (list, tuple)):
        return {str(cls_name): {} for cls_name in raw_classes}
    return {}


class TrustGraphGovernorEngine:
    """Pure-Python micro-kernel engine enforcing TrustGraph architecture invariants."""

    def evaluate_shacl_policy_filter(
        self,
        triples: list[dict[str, str]] | tuple[dict[str, str], ...],
        policies: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        subject_attributes: dict[str, dict[str, Any]] | None = None,
    ) -> ShaclPolicyFilterReport:
        """Filter triples by subject IRI via sh:order-sorted, first-match-wins SHACL-AF shapes."""
        cache_limits = {
            "query_cache_ttl_s": QUERY_CACHE_TTL_SECONDS,
            "query_cache_max": QUERY_CACHE_MAX_ENTRIES,
            "sparql_cache_max": SPARQL_CACHE_MAX_ENTRIES,
            "node_cache_ttl_s": NODE_CACHE_TTL_SECONDS,
            "node_cache_max": NODE_CACHE_MAX_ENTRIES,
        }
        normalized_triples = tuple(dict(t) for t in triples)
        if not policies:
            return ShaclPolicyFilterReport(
                open_mode=True,
                evaluated_policies=(),
                blocked_subjects=(),
                allowed_triples=normalized_triples,
                dropped_triples=(),
                policy_evaluations=(),
                cache_limits=cache_limits,
            )

        sorted_policies = sorted(
            policies,
            key=lambda p: (
                int(p.get("order")) if p.get("order") is not None else DEFAULT_POLICY_ORDER,
                str(p.get("shape_uri") or p.get("uri") or p.get("name") or ""),
            ),
        )
        policy_names = tuple(
            str(p.get("shape_uri") or p.get("uri") or p.get("name") or f"{POLICY_GRAPH_URI}#shape-{idx}")
            for idx, p in enumerate(sorted_policies)
        )

        attrs_map = subject_attributes or {}
        seen_subjects: list[str] = []
        seen_set: set[str] = set()
        for triple in normalized_triples:
            subj = _extract_subject(triple)
            if subj and subj not in seen_set:
                seen_set.add(subj)
                seen_subjects.append(subj)

        blocked_subjects: list[str] = []
        blocked_set: set[str] = set()
        evaluations: list[dict[str, Any]] = []

        for subj in seen_subjects:
            attrs = attrs_map.get(subj) or {}
            matched = False
            for idx, policy in enumerate(sorted_policies):
                if _policy_matches_subject(policy, subj, attrs):
                    shape_id = policy_names[idx]
                    order_val = int(policy.get("order")) if policy.get("order") is not None else DEFAULT_POLICY_ORDER
                    blocks = bool(policy.get("blocks", True))
                    evaluations.append(
                        {
                            "subject": subj,
                            "policy": shape_id,
                            "order": order_val,
                            "blocks": blocks,
                        }
                    )
                    if blocks and subj not in blocked_set:
                        blocked_set.add(subj)
                        blocked_subjects.append(subj)
                    matched = True
                    break
            if not matched:
                evaluations.append({"subject": subj, "policy": None, "order": None, "blocks": False})

        allowed: list[dict[str, str]] = []
        dropped: list[dict[str, str]] = []
        for triple in normalized_triples:
            if _extract_subject(triple) in blocked_set:
                dropped.append(triple)
            else:
                allowed.append(triple)

        return ShaclPolicyFilterReport(
            open_mode=False,
            evaluated_policies=policy_names,
            blocked_subjects=tuple(blocked_subjects),
            allowed_triples=tuple(allowed),
            dropped_triples=tuple(dropped),
            policy_evaluations=tuple(evaluations),
            cache_limits=cache_limits,
        )

    def validate_ontology_extractions(
        self,
        ontology: dict[str, Any],
        triples: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        bypass_selector_below: int = DEFAULT_BYPASS_SELECTOR_BELOW,
        top_k: int = DEFAULT_SELECTOR_TOP_K,
        similarity_threshold: float = DEFAULT_SELECTOR_SIMILARITY_THRESHOLD,
    ) -> OntologyValidationReport:
        """Validate extracted relationship & attribute triples with small-schema bypass and subClassOf closure."""
        _ = (top_k, similarity_threshold)  # Preserved for OntologySelector parity
        classes = _normalize_classes_map(ontology.get("classes"))
        obj_props = dict(ontology.get("object_properties") or {})
        data_props = dict(ontology.get("datatype_properties") or {})
        total_elements = len(classes) + len(obj_props) + len(data_props)
        selector_bypassed = total_elements < bypass_selector_below

        cycles: list[str] = []
        cycle_set: set[str] = set()

        def get_ancestors(cls_name: str) -> set[str]:
            ancestors: set[str] = set()
            queue: deque[str] = deque([cls_name])
            visited_local: set[str] = {cls_name}
            while queue:
                current = queue.popleft()
                cls_def = classes.get(current) or {}
                raw_parents = cls_def.get("subClassOf") or cls_def.get("parent") or cls_def.get("superclasses") or []
                parents = [raw_parents] if isinstance(raw_parents, str) else list(raw_parents)
                for parent in parents:
                    parent_str = str(parent)
                    if parent_str == current or parent_str in ancestors or parent_str in visited_local:
                        if parent_str not in cycle_set:
                            cycle_set.add(parent_str)
                            cycles.append(parent_str)
                        continue
                    ancestors.add(parent_str)
                    visited_local.add(parent_str)
                    queue.append(parent_str)
            return ancestors

        def matches_class(entity_type: str | None, required: str | None) -> bool:
            if not required:
                return True
            if not entity_type:
                return False
            if entity_type == required:
                return True
            return required in get_ancestors(entity_type)

        # Prime cycle detection over declared classes even if triple list is empty.
        for cls_name in classes:
            get_ancestors(cls_name)

        accepted: list[dict[str, str]] = []
        rejected: list[dict[str, Any]] = []
        violations: list[str] = []

        for raw_triple in triples:
            triple = dict(raw_triple)
            pred = str(triple.get("predicate") or triple.get("p") or "")
            kind = str(triple.get("kind") or "")
            if not kind:
                if pred in obj_props or "object_type" in triple:
                    kind = "relationship"
                elif pred in data_props or "entity_type" in triple or "value" in triple:
                    kind = "attribute"

            if kind == "relationship":
                spec = obj_props.get(pred)
                if spec is None:
                    reason = f"unknown_object_property:{pred}"
                    rejected.append({**triple, "reason": reason})
                    violations.append(reason)
                    continue
                subj_type = triple.get("subject_type")
                obj_type = triple.get("object_type")
                domain_req = spec.get("domain")
                range_req = spec.get("range")
                if not matches_class(subj_type, domain_req):
                    reason = f"domain_mismatch:{pred}:{subj_type}!={domain_req}"
                    rejected.append({**triple, "reason": reason})
                    violations.append(reason)
                    continue
                if not matches_class(obj_type, range_req):
                    reason = f"range_mismatch:{pred}:{obj_type}!={range_req}"
                    rejected.append({**triple, "reason": reason})
                    violations.append(reason)
                    continue
                accepted.append(
                    {
                        "s": str(triple.get("subject") or triple.get("s") or ""),
                        "p": pred,
                        "o": str(triple.get("object") or triple.get("o") or ""),
                    }
                )
            elif kind == "attribute":
                spec = data_props.get(pred)
                if spec is None:
                    reason = f"unknown_datatype_property:{pred}"
                    rejected.append({**triple, "reason": reason})
                    violations.append(reason)
                    continue
                entity_type = triple.get("entity_type") or triple.get("subject_type")
                domain_req = spec.get("domain")
                if not matches_class(entity_type, domain_req):
                    reason = f"domain_mismatch:{pred}:{entity_type}!={domain_req}"
                    rejected.append({**triple, "reason": reason})
                    violations.append(reason)
                    continue
                accepted.append(
                    {
                        "s": str(triple.get("subject") or triple.get("s") or ""),
                        "p": pred,
                        "o": str(triple.get("value") if "value" in triple else triple.get("o") or ""),
                    }
                )
            else:
                reason = f"unknown_property:{pred}"
                rejected.append({**triple, "reason": reason})
                violations.append(reason)

        return OntologyValidationReport(
            total_elements=total_elements,
            selector_bypassed=selector_bypassed,
            bypass_threshold=bypass_selector_below,
            accepted_triples=tuple(accepted),
            rejected_triples=tuple(rejected),
            cycles_detected=tuple(cycles),
            violations=tuple(violations),
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
        """Build dual-named-graph extraction & 5-stage query explainability PROV-O traces."""
        qid = question_id.strip()
        if not qid:
            raise ValueError("question_id must be non-empty")

        question_uri = f"{EXPLAINABILITY_URN_PREFIX}question:{qid}"
        stage_uris = {
            stage: (question_uri if stage == "question" else f"{EXPLAINABILITY_URN_PREFIX}prov:{stage}:{qid}")
            for stage in EXPLAINABILITY_STAGES
        }

        ext_list: list[dict[str, str]] = [
            {
                "s": str(t.get("s") or ""),
                "p": str(t.get("p") or ""),
                "o": str(t.get("o") or ""),
                "g": SOURCE_GRAPH_URI,
            }
            for t in extraction_triples
        ]
        if document_id:
            doc_uri = f"{EXTRACTION_PROVENANCE_PREFIX}doc/{document_id.strip()}"
            ext_list.append(
                {
                    "s": doc_uri,
                    "p": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                    "o": "http://www.w3.org/ns/prov#Entity",
                    "g": SOURCE_GRAPH_URI,
                }
            )

        details = stage_details or {}
        explain_list: list[dict[str, str]] = [
            {
                "s": question_uri,
                "p": "http://www.w3.org/2000/01/rdf-schema#label",
                "o": query_text,
                "g": RETRIEVAL_GRAPH_URI,
            }
        ]
        prev_uri = question_uri
        for stage in EXPLAINABILITY_STAGES[1:]:
            stage_uri = stage_uris[stage]
            explain_list.append(
                {
                    "s": stage_uri,
                    "p": "http://www.w3.org/ns/prov#wasDerivedFrom",
                    "o": prev_uri,
                    "g": RETRIEVAL_GRAPH_URI,
                }
            )
            if stage in details:
                explain_list.append(
                    {
                        "s": stage_uri,
                        "p": "http://www.w3.org/2000/01/rdf-schema#comment",
                        "o": str(details[stage]),
                        "g": RETRIEVAL_GRAPH_URI,
                    }
                )
            prev_uri = stage_uri

        computed_total = total_tokens if total_tokens is not None else prompt_tokens + completion_tokens
        append_tokens = prompt_tokens > 0 or completion_tokens > 0 or computed_total > 0
        if append_tokens:
            synth_uri = stage_uris["synthesis"]
            explain_list.extend(
                [
                    {
                        "s": synth_uri,
                        "p": f"{EXPLAINABILITY_URN_PREFIX}token/prompt",
                        "o": str(max(0, prompt_tokens)),
                        "g": RETRIEVAL_GRAPH_URI,
                    },
                    {
                        "s": synth_uri,
                        "p": f"{EXPLAINABILITY_URN_PREFIX}token/completion",
                        "o": str(max(0, completion_tokens)),
                        "g": RETRIEVAL_GRAPH_URI,
                    },
                    {
                        "s": synth_uri,
                        "p": f"{EXPLAINABILITY_URN_PREFIX}token/total",
                        "o": str(max(0, computed_total)),
                        "g": RETRIEVAL_GRAPH_URI,
                    },
                ]
            )

        return ProvenanceTraceEnvelope(
            question_id=qid,
            source_graph=SOURCE_GRAPH_URI,
            retrieval_graph=RETRIEVAL_GRAPH_URI,
            question_uri=question_uri,
            stage_uris=stage_uris,
            extraction_triples=tuple(ext_list),
            explainability_triples=tuple(explain_list),
            token_triples_appended=append_tokens,
            total_tokens=max(0, computed_total),
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
        """Calibrate temperature, normalize probabilities, compute entropy confidence & option budget."""
        if question_type not in LAYA_QUESTION_TYPES:
            raise ValueError(f"Unsupported Laya question_type {question_type!r}; expected {tuple(LAYA_QUESTION_TYPES)}")
        if not logits_or_probs:
            raise ValueError("logits_or_probs must be non-empty")

        clamped_temp = _clamp_temperature(temperature)
        bucket = _temp_bucket(clamped_temp, num_buckets=temp_buckets)

        raw_vals = [float(x) for x in logits_or_probs]
        if probs_already_normalized:
            clipped = [max(0.0, x) for x in raw_vals]
            total = sum(clipped)
            if total <= 0.0:
                probs = tuple(1.0 / len(clipped) for _ in clipped)
            else:
                probs = tuple(round(x / total, 6) for x in clipped)
        else:
            scaled = [x / clamped_temp for x in raw_vals]
            max_scaled = max(scaled)
            exps = [math.exp(x - max_scaled) for x in scaled]
            denom = sum(exps)
            probs = tuple(round(e / denom, 6) for e in exps)

        selected_index = max(range(len(probs)), key=lambda idx: probs[idx])
        entropy, confidence = _confidence_from_probs(probs)

        k = len(options) if options else len(probs)
        capped_opt = min(LAYA_OPTION_TOKEN_CAP, max(0, int(option_tokens_each)))
        opt_budget = LAYA_HEAD_MAX_LEN - k * (1 + capped_opt)
        shrink_warning = opt_budget < LAYA_MIN_OPT_BUDGET

        violations: list[str] = []
        if options and len(options) != len(probs):
            violations.append(f"options_length_mismatch:{len(options)}!={len(probs)}")
        if question_tokens > LAYA_MAX_SEQ_LEN:
            violations.append(f"question_tokens_exceeds_max_seq_len:{question_tokens}>{LAYA_MAX_SEQ_LEN}")

        return LayaDecisionScoreReport(
            question_type=question_type,
            qtype_id=LAYA_QUESTION_TYPES[question_type],
            raw_temperature=float(temperature),
            clamped_temperature=clamped_temp,
            temp_bucket=bucket,
            probabilities=probs,
            selected_index=selected_index,
            entropy=entropy,
            confidence=confidence,
            opt_budget=opt_budget,
            head_max_len=LAYA_HEAD_MAX_LEN,
            max_seq_len=LAYA_MAX_SEQ_LEN,
            shrink_warning=shrink_warning,
            violations=tuple(violations),
        )
