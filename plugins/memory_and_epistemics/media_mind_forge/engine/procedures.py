"""Forge procedural lens: Shu-Ha-Ri execution stages, diagnostic rubrics, and anti-patterns."""

from __future__ import annotations

from ..models import (
    AntiPatternItem,
    DiagnosticQuestion,
    ProceduralStage,
)


def synthesize_procedural_stages() -> list[ProceduralStage]:
    """Synthesize complete Shu-Ha-Ri execution stages with verifiable completion criteria."""
    return [
        ProceduralStage(
            stage_num=1,
            name="Competency Scoping & Boundary Definition",
            objective="Formulate explicit natural-language competency questions defining the questions the knowledge model must answer.",
            completion_criterion="Exhaustive list of verifiable competency questions agreed upon and documented.",
            action_steps=[
                "Interview domain experts and end-user personas to capture core tasks",
                "Formulate 5 to 15 concrete competency questions with expected query outputs",
                "Define strict out-of-scope boundaries to prevent domain creep",
            ],
        ),
        ProceduralStage(
            stage_num=2,
            name="Conceptual & Taxonomical Partitioning",
            objective="Identify core domain entities, relationships, and taxonomical subsumption hierarchies.",
            completion_criterion="Formal concept glossary and normalized entity taxonomies established.",
            action_steps=[
                "Extract candidate domain entities from requirements and texts",
                "Cluster synonyms and establish canonical vocabulary",
                "Structure taxonomical 'is-a' subsumption hierarchies",
            ],
        ),
        ProceduralStage(
            stage_num=3,
            name="Formal Axiomatization & Relationship Modeling",
            objective="Define property domains, ranges, disjointness constraints, and inverse relationships.",
            completion_criterion="Syntactically valid OWL/RDFS schema with explicit semantic axioms.",
            action_steps=[
                "Declare object properties connecting entity classes",
                "Enforce domain and range restrictions",
                "Assert disjoint classes to prevent accidental model subsumption",
            ],
        ),
        ProceduralStage(
            stage_num=4,
            name="Logical Evaluation & Reasoner Verification",
            objective="Execute automated description logic reasoning and verify competency question satisfaction.",
            completion_criterion="HermiT or Pellet reasoner consistency check succeeds with zero contradictory models.",
            action_steps=[
                "Run DL reasoner to detect unsatisfiable classes and cycles",
                "Translate competency questions into SPARQL queries against sample dataset",
                "Verify query responses against expected ground-truth answers",
            ],
        ),
        ProceduralStage(
            stage_num=5,
            name="Knowledge Vault Catalog Integration",
            objective="Package schema artifacts, isnad provenance, and executable coaching cards into repo memory.",
            completion_criterion="Dual-file Knowledge Item committed to vault with verified isnad lineage.",
            action_steps=[
                "Generate companion CARD.md with single-pipe ASCII table",
                "Commit metadata.json and summary.md to .harness/knowledge/",
                "Export schema diagram and register in knowledge graph catalog",
            ],
        ),
    ]


def synthesize_diagnostic_rubric() -> list[DiagnosticQuestion]:
    """Synthesize diagnostic coaching probes to evaluate knowledge models against domain standards."""
    return [
        DiagnosticQuestion(
            question="Can every declared class and predicate be traced to at least one audited competency question?",
            rationale="Prevents speculative modeling and bloat per Gruber's Minimal Commitment principle.",
            passing_criteria="Unbroken 1-to-1 or 1-to-N mapping between schema entities and competency questions.",
            failing_indicators=[
                "Classes with zero instance usage in test queries",
                "Dangling speculative properties added 'just in case'",
            ],
        ),
        DiagnosticQuestion(
            question="Does the class hierarchy strictly preserve formal 'is-a' subsumption transitivity?",
            rationale="Violating transitivity introduces logical inconsistency and reasoner failures.",
            passing_criteria="Every instance of a subclass is unquestionably an instance of the superclass.",
            failing_indicators=[
                "Confusing part-whole relationships (part-of) with subclassing (is-a)",
                "Subclasses that negate parent class properties",
            ],
        ),
        DiagnosticQuestion(
            question="Is the model free of syntactic encoding bias tied to a specific syntax?",
            rationale="Ensures the conceptual model survives migration across serialization languages and graph stores.",
            passing_criteria="Conceptual schema can be rendered identically in Turtle, JSON-LD, or relational SQL.",
            failing_indicators=[
                "Introducing dummy classes solely to satisfy tool-specific layout requirements",
            ],
        ),
    ]


def synthesize_anti_patterns() -> list[AntiPatternItem]:
    """Synthesize explicit failure modes paired with invariant behavioral defenses."""
    return [
        AntiPatternItem(
            name="Speculative Over-Commitment",
            telltale_symptom="Declaring exhaustive taxonomies and deeply nested hierarchies that have no immediate query requirements.",
            positive_rule="Enforce Gruber's Minimal Commitment: model only what is strictly necessary to answer verified competency questions.",
            risk_level="HIGH",
        ),
        AntiPatternItem(
            name="Part-Whole Subclass Confusion",
            telltale_symptom="Declaring a component part as a subclass of the whole (e.g. Engine is-a Car instead of Engine part-of Car).",
            positive_rule="Strictly verify that every instance of the child class is universally an instance of the parent class.",
            risk_level="CRITICAL",
        ),
        AntiPatternItem(
            name="Monolithic Coupling",
            telltale_symptom="Bundling disparate domain concepts into a single mega-schema that cannot be reused independently.",
            positive_rule="Partition schemas into modular, single-responsibility sub-ontologies connected by explicit foreign keys.",
            risk_level="HIGH",
        ),
    ]
