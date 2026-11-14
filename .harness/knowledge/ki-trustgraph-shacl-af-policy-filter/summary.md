# TrustGraph: SHACL-AF Subject-IRI Policy Filter & Bounded Caches

## Overview
- **Source Repository**: `https://github.com/trustgraph-ai/trustgraph` (`17e5d742`)
- **Primary Files**:
  - `trustgraph-flow/trustgraph/policy/policy_filter.py#L1-L410`
  - `trustgraph-flow/trustgraph/policy/policy_filter.py#L615-L865`

## Core Architecture & Invariants
1. **Dedicated Policy Named Graph (`POLICY_GRAPH`)**: Policy shapes live in `urn:graph:policy`, isolating access-control metadata from user knowledge graphs (`urn:graph:source` and `urn:graph:retrieval`).
2. **Deterministic Rule Precedence (`sh:order`)**: `LoadedPolicy` rules sort ascending by integer `sh:order` (defaulting to `99`), with tie-breaking by shape IRI. Evaluation applies strict **first-match-wins** semantics where `tg-pol:blocks` defaults to `True`.
3. **Subject-IRI Filtering (`PolicyFilter`)**: Candidate subject IRIs are checked against ordered rules; any triple whose subject `s` evaluates as blocked is stripped before downstream retrieval or synthesis.
4. **Bounded Multi-Tier Caches**: Query decisions cache with `QUERY_CACHE_TTL = 30` and `QUERY_CACHE_MAX = 256`, SPARQL AST/results cap at `SPARQL_CACHE_MAX = 64`, and node attributes cache with `NODE_CACHE_TTL = 60` and `NODE_CACHE_MAX = 1024`.
5. **Explicit Open-Mode Semantics**: When no `sh:NodeShape` policies are registered in `urn:graph:policy`, `PolicyFilter` operates in explicit open mode rather than silently misconfiguring partial filters.

## Decision Heuristics & Anti-Patterns
- **Never evaluate unordered policy rules**: Always sort ascending by `sh:order` (default `99`) and preserve the first matching rule.
- **Never assume unbounded policy/SPARQL caches in streaming triple pipelines**: Enforce TTL and max-entry caps on query, SPARQL, and node caches.
