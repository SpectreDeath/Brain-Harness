# Google Research `gfsa`: Graph Finite-State Automaton Layer

## 1. Context & Provenance

- **Upstream Repository**: `https://github.com/google-research/google-research` (`gfsa/`)
- **Snapshot Reference**: `google-research-master` (archive snapshot, non-git)
- **Publication**: *Learning Graph Structure With A Finite-State Automaton Layer* (NeurIPS 2020, `https://arxiv.org/abs/2007.04929`)
- **Primary Verified Sources**:
  - `gfsa/README.md` (`L1-L90`)
  - `gfsa/automaton_builder.py` (`L42-L95`, sha256 `a69088505448a104d8b5d5a5b51d4a6f91f31c9433addff4f14a54228fd6e7e7`)
  - `gfsa/linear_solvers.py` (`L27-L78`, sha256 `1f4caa57351c4e48065185c6ab5476504653689eed527867899635d3e488808d`)

## 2. Core Architectural Invariants

1. **Typed Edge-Conditioned Automaton Routes (`automaton_builder.py`)**: Transitions condition on immutable `(node_type, in_edge)` observations (`InRouteType`) and emit distributions over `(node_type, in_edge, out_edge)` (`InOutRouteType`) plus `SpecialActions` (`FINISH`, `BACKTRACK`, `FAIL`), initialized at sentinel `SOURCE_INITIAL`.
2. **Implicit Equilibrium Differentiation (`linear_solvers.py`)**: Expected state visits `(I - P)^{-1} b` are solved iteratively via `richardson_solve` inside `jax.lax.fori_loop` and wrapped in `jax.lax.custom_linear_solve`, decoupling gradient computation from forward iteration depth.

## 3. Applicability to Brain Harness

- Directly informs AST static-analysis and typed graph traversal seams (`Rule 9` AST RepoMap & `ontology-spider` predicate-typed walks).
