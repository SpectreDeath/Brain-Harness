# Guarino's Precision vs. Coverage Tradeoff in Knowledge Representation

**ID:** `ki_guarino_precision_coverage_tradeoff`  
**Category:** `data_modeling`  
**Origin:** `https://www.youtube.com/watch?v=RHjoCpNj3KQ` (Prof. Dr. Harald Sack)  
**Provenance Lineage:** `https://www.youtube.com/watch?v=RHjoCpNj3KQ#t=600`, `outputs/transcripts/RHjoCpNj3KQ_transcript.json`

## Executive Summary
Nicola Guarino established that knowledge representation is governed by a fundamental tension between **Precision** and **Coverage**:
- **Precision**: The degree to which an ontology constrains possible interpretations to only intended models, ruling out unintended or false interpretations through formal logical axioms.
- **Coverage**: The breadth and domain span of entities, relations, and scenarios captured by the model.

## Architectural Invariants & Rules
1. **Precision Overhead**: High precision requires formal expressivity (e.g. OWL 2 DL / description logic axioms), significantly increasing reasoner compute overhead and complexity.
2. **Coverage Ambiguity**: High coverage with low precision (e.g., loose RDF schemas, simple tagging) scales rapidly across distributed systems but permits false or unintended interpretations.
3. **Engineering Balance**: Calibrate precision and coverage based on downstream task requirements rather than dogmatically maximizing axiomatic rigor.
