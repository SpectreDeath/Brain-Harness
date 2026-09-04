---
name: ontological-engineering-coach
description: Master Ontological Engineering & Knowledge Graph Modeling using principles distilled from Prof. Dr. Harald Sack. Use when designing domain ontologies, auditing knowledge graphs, applying Gruber's criteria, or balancing precision vs coverage.
---

# Ontological Engineering Coach

`ontological-engineering-coach` is an executable cognitive workflow engine derived from *Ontological Engineering & Knowledge Graph Modeling* presented by Prof. Dr. Harald Sack.

Every execution adheres to three foundational craft pillars:
1. **The Visual Brief** — Interactive HTML reports generated in `%TEMP%` rendering ontology schemas and competence DAGs.
2. **The Mandatory Checkpoint** — Explicit human-in-the-loop gates (`RequestFeedback: true`) before modifying domain schemas.
3. **Explicit Anti-Patterns** — Rigid behavioral boundaries eliminating speculative over-commitment and taxonomy confusion.

See [CARD.md](CARD.md) for the summary card and completion checklist.

---

## Execution Sequence

### Stage 1: Competency Scoping & Boundary Definition

Formulate explicit natural-language competency questions defining the questions the knowledge model must answer.

- Interview domain experts and end-user personas to capture core tasks
- Formulate 5 to 15 concrete competency questions with expected query outputs
- Define strict out-of-scope boundaries to prevent domain creep

> **Completion criterion**: Exhaustive list of verifiable competency questions agreed upon and documented.

---

### Stage 2: Taxonomy & Class Hierarchy Construction

Draft the core subsumption hierarchy and relationship predicates satisfying audited competency queries.

- Extract primary domain entities into disjoint or subsumed classes
- Assign domain and range constraints to relational predicates
- Verify subclass relationships obey strict 'is-a' transitivity

> **Completion criterion**: Directed Acyclic Graph (DAG) of class hierarchies verified free of cycles.

---

### Stage 3: Gruber 5-Axis Quality Audit

Evaluate candidate schema against Clarity, Coherence, Extendibility, Minimal Bias, and Minimal Commitment.

- Run reasoner consistency check (HermiT or Pellet) to confirm formal coherence
- Audit class definitions for unambiguous, objective definitions (clarity)
- Verify representation independence (minimal encoding bias)
- Prune unused classes or axioms (minimal ontological commitment)

> **Completion criterion**: Scored evaluation matrix with zero critical violations across all 5 criteria.

---

### Stage 4: Competency Verification & Query Validation

Translate competency questions into SPARQL queries and verify expected result sets against sample instance graphs.

- Instantiate representative test instance data
- Author SPARQL test assertions mirroring original competency questions
- Validate query execution latency and result fidelity

> **Completion criterion**: 100% of competency questions execute with non-empty, semantically correct answer sets.

---

### Stage 5: Modularization & Lineage Documentation

Partition ontology into composable modules and author persistent documentation and CARD summary.

- Decompose monolithic ontologies into modular sub-domain schemas
- Add owl:versionInfo, rdfs:label, and rdfs:comment metadata
- Export schema diagram and register in knowledge graph catalog

> **Completion criterion**: Versioned ontology artifact with metadata annotations and schema diagrams published.

---

## Anti-Patterns

- **Speculative Over-Commitment** — Declaring exhaustive taxonomies and deeply nested hierarchies that have no immediate query requirements. Enforce Gruber's Minimal Commitment: model only what is strictly necessary to answer verified competency questions.
- **Part-Whole Subclass Confusion** — Declaring a component part as a subclass of the whole (e.g. Engine is-a Car instead of Engine part-of Car). Strictly verify that every instance of the child class is universally an instance of the parent class.
- **Monolithic Coupling** — Bundling disparate domain concepts into a single mega-schema that cannot be reused independently. Partition schemas into modular, single-responsibility sub-ontologies connected by explicit foreign keys.
