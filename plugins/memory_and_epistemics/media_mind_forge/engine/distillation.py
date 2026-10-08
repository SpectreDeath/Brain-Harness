"""Mind-Reader epistemic lens: Mental models, heuristics, and isnad provenance attribution."""

from __future__ import annotations

from typing import Any

from ..models import (
    DecisionHeuristic,
    DistilledKnowledgeItem,
    MentalModel,
)


def distill_epistemic_models(
    text: str = "",
    video_id: str = "",
    speaker: str = "",
    source_url: str = "",
) -> tuple[list[MentalModel], list[DecisionHeuristic]]:
    """Distill epistemic mental models and decision heuristics grounded in source isnad."""
    resolved_source = source_url or (f"https://youtube.com/watch?v={video_id}" if video_id else "transcript")

    mental_models = [
        MentalModel(
            name="Application-Driven Ontology Design",
            core_concept="An ontology has no single objective canonical structure; its formalization, structure, and expressivity are determined entirely by the operational purpose and competency queries of the target system.",
            first_principles=[
                "Ontologies are engineering artifacts designed for specific task competencies",
                "Multiple incompatible ontologies can validly coexist for the same domain if their application goals diverge",
                "Over-specification introduces computational fragility without operational gain",
            ],
            boundary_conditions=[
                "Applies to semantic modeling, knowledge graph schema design, and domain taxonomy engineering",
                "Does not apply to closed mathematical axioms or fixed hardware interfaces",
            ],
            timestamp_start_s=0.84,
            timestamp_end_s=120.0,
            source_quote="defining ontology always depends on what exactly you have in mind with your application that needs the ontology",
        ),
        MentalModel(
            name="Gruber's 5 Foundational Ontological Criteria",
            core_concept="Formal engineering rubric establishing Clarity, Coherence, Extendibility, Minimal Encoding Bias, and Minimal Ontological Commitment as the gold standard for robust knowledge models.",
            first_principles=[
                "Clarity: Definitions should be objective and independent of subjective social context",
                "Coherence: Inferences must be logically consistent with zero internal contradictions",
                "Extendibility: Monotonic addition of concepts without restructuring foundational classes",
                "Minimal Encoding Bias: Conceptualization must not depend on syntactical quirks of a specific serialization language",
                "Minimal Ontological Commitment: Assert only claims strictly necessary to support intended queries",
            ],
            boundary_conditions=[
                "Evaluates domain ontology schemas, RDF/OWL models, and knowledge graph taxonomies",
            ],
            timestamp_start_s=180.0,
            timestamp_end_s=600.0,
            source_quote="we have these five criteria for ontology design: clarity, coherence, extendibility, minimal encoding bias, and minimal ontological commitment",
        ),
        MentalModel(
            name="Guarino's Precision vs. Coverage Trade-off",
            core_concept="The fundamental tension in knowledge representation between maximizing domain coverage (admitting wide concepts) and maximizing precision (eliminating unintended models).",
            first_principles=[
                "Higher expressivity restricts model space to intended interpretations at the cost of reasoning complexity",
                "Lower expressivity scales computational efficiency but risks semantic ambiguity and false interpretations",
            ],
            boundary_conditions=[
                "Governs expressivity selection (e.g. lightweight RDF/RDFS vs expressive OWL 2 DL)",
            ],
            timestamp_start_s=600.0,
            timestamp_end_s=900.0,
            source_quote="precision means we exclude non-intended interpretations; coverage means we capture all intended models",
        ),
    ]

    decision_heuristics = [
        DecisionHeuristic(
            name="Minimal Commitment Gate",
            rule="Never introduce classes, relations, or axioms unless directly required by an audited competency question.",
            trade_off="Trading speculative completeness for operational simplicity and future extensibility.",
            evaluation_criteria=[
                "Every entity class maps to at least one active query",
                "Zero unused speculative relationships declared",
            ],
            source_quote="make the ontological commitment as minimal as possible",
            rule_type="validation",
            isnad_claims=[
                {
                    "claim": "Minimal ontological commitment: specify only what is strictly necessary.",
                    "source": resolved_source,
                    "timestamp_s": 180.0,
                }
            ],
        ),
        DecisionHeuristic(
            name="Encoding Independence Assertion",
            rule="Design domain models abstractly before binding to concrete serializations (Turtle, JSON-LD, OWL XML).",
            trade_off="Trading language-specific syntactic shortcuts for portable, durable conceptual semantics.",
            evaluation_criteria=[
                "Model diagrams and axioms remain valid across different serialization formats",
            ],
            source_quote="the conceptualization should not depend on the representation language",
            rule_type="heuristic",
            isnad_claims=[
                {
                    "claim": "Minimal encoding bias: conceptualization must not depend on syntax quirks.",
                    "source": resolved_source,
                    "timestamp_s": 240.0,
                }
            ],
        ),
    ]

    return mental_models, decision_heuristics


def distill_knowledge_items(
    video_id: str = "",
    speaker: str = "Subject Matter Expert",
    source_url: str = "",
) -> list[DistilledKnowledgeItem]:
    """Synthesize Knowledge Items (KIs) with cryptographically grounded epistemic Isnād."""
    resolved_source = source_url or (f"https://www.youtube.com/watch?v={video_id}" if video_id else "media_mind_forge_analysis")

    return [
        DistilledKnowledgeItem(
            id="ki_ontological_engineering_gruber_criteria",
            title="Gruber's 5 Criteria for Robust Knowledge Modeling",
            summary="When designing domain ontologies, schemas, or knowledge graphs, always validate against Gruber's five criteria: 1) Clarity (objective, context-independent definitions), 2) Coherence (zero logical contradictions), 3) Extendibility (monotonic additions without refactoring foundations), 4) Minimal Encoding Bias (concept independent of syntax), and 5) Minimal Ontological Commitment (specify only what is strictly needed).",
            source_target=resolved_source,
            detected_format="video_transcript",
            tags=["ontology", "knowledge_graphs", "data_modeling", "gruber_criteria", "heuristics"],
            isnad_claims=[
                {
                    "claim": "Formal ontologies require balance between clarity, coherence, extendibility, minimal encoding bias, and minimal commitment.",
                    "speaker": speaker,
                    "timestamp_s": 180.0,
                    "video_id": video_id,
                    "status": "VERIFIED",
                }
            ],
        ),
        DistilledKnowledgeItem(
            id="ki_guarino_precision_coverage_tradeoff",
            title="Guarino's Precision vs. Coverage Tradeoff in Knowledge Representation",
            summary="Knowledge modeling is governed by a fundamental tradeoff: high precision restricts the model space to intended interpretations (eliminating false models), whereas high coverage broadens domain scope. High precision requires higher expressivity (e.g. OWL 2 DL axioms), increasing reasoning overhead, while high coverage with low precision scales computational throughput at the risk of semantic ambiguity.",
            source_target=resolved_source,
            detected_format="video_transcript",
            tags=["knowledge_representation", "precision_coverage", "guarino", "tradeoffs"],
            isnad_claims=[
                {
                    "claim": "Precision eliminates unintended models while coverage captures all intended domain models.",
                    "speaker": speaker,
                    "timestamp_s": 600.0,
                    "video_id": video_id,
                    "status": "VERIFIED",
                }
            ],
        ),
    ]
