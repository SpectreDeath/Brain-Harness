# TrustGraph: OntologyRAG Small-Schema Bypass & Cycle-Safe Subclass Validation

## Overview
- **Source Repository**: `https://github.com/trustgraph-ai/trustgraph` (`17e5d742`)
- **Primary Files**:
  - `trustgraph-flow/trustgraph/extract/kg/ontology/ontology_selector.py#L20-L160`
  - `trustgraph-flow/trustgraph/extract/kg/ontology/triple_converter.py#L21-L240`

## Core Architecture & Invariants
1. **Small-Schema Bypass Gate (`OntologySelector`)**: Computes `total_elements = len(classes) + len(object_properties) + len(datatype_properties)`. When `total_elements < bypass_selector_below` (default `5`), the entire `OntologySubset` is passed directly without embedding-similarity filtering (`top_k=10`, `similarity_threshold=0.3`), eliminating false negatives on compact schemas.
2. **Cycle-Safe Ancestor Traversal (`_get_ancestor_classes`)**: Collects transitive `subClassOf` ancestors while tracking visited class IDs (`parent in ancestors` guard) to guarantee termination on malformed or cyclic class hierarchies.
3. **Relationship Domain & Range Checks (`convert_relationship`)**: Verifies `subject_type` against property `domain` (using subclass closure via `_matches_class_constraint`) AND `object_type` against property `range`; rejects mismatched triples cleanly with structured diagnostics.
4. **Attribute Domain Checks (`convert_attribute`)**: Verifies `entity_type` satisfies datatype property `domain` via subclass closure prior to emitting literal attribute triples.

## Decision Heuristics & Anti-Patterns
- **Never run lossy vector ontology selection on tiny schemas**: Short-circuit to full ontology retention below `bypass_selector_below = 5`.
- **Never recurse `subClassOf` chains without a visited set**: Cyclic ontology definitions will cause infinite recursion.
