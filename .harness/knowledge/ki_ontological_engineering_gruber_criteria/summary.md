# Gruber's 5 Criteria for Robust Knowledge Modeling

**ID:** `ki_ontological_engineering_gruber_criteria`  
**Category:** `data_modeling`  
**Origin:** `https://www.youtube.com/watch?v=RHjoCpNj3KQ` (Prof. Dr. Harald Sack)  
**Provenance Lineage:** `https://www.youtube.com/watch?v=RHjoCpNj3KQ#t=180`, `outputs/transcripts/RHjoCpNj3KQ_transcript.json`

## Executive Summary
When designing domain ontologies, schemas, or knowledge graphs, always validate models against Thomas Gruber's five core design criteria:
1. **Clarity**: Definitions should be objective, clear, and context-independent without ambiguous jargon.
2. **Coherence**: Definitions and axioms must be logically consistent; inferences must never lead to contradictions.
3. **Extendibility**: An ontology should offer a conceptual foundation for a range of anticipated tasks, allowing monotonic additions without requiring revision of existing definitions.
4. **Minimal Encoding Bias**: Conceptualization should be specified at the knowledge level without depending on a specific representation syntax or encoding scheme.
5. **Minimal Ontological Commitment**: An ontology should make as few claims as possible about the world being modeled, giving parties the freedom to specialize and instantiate according to their local needs.

## Architectural Invariants & Rules
1. **Minimal Commitment Gate**: Before finalizing an ontology or schema, verify that every class, property, and relation directly answers a scoped competency question.
2. **Representation Independence**: Avoid embedding database-specific or serialization-specific constructs into high-level conceptual models.
