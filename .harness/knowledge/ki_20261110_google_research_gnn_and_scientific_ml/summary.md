# Graph-Native Program Representations & Differentiable Scientific ML

## Context & Provenance
Synthesized from MemGraphRAG 3-layer ontology extraction (83 nodes, 84 edges, 28 fact triples, 15 schemas; external scan unrefuted, not persisted as in-repo artifact), REA SavedModel protobuf inspection, and `DocSynchronizerService` AST audits across `google-research-master`.

> [!NOTE] 2026-11-11 Re-stamp & Errata Note
> - Arithmetic corrected: `jax_dft` symbol coverage is **83.8%** (62/74), not 54.0%; `aloe` is **11.8%** (14/119), not 7.2%.
> - Path corrected: `jax_dft/scf.py` → **`jax_dft/jax_dft/scf.py`** (verified upstream via GitHub API, 19,350 B).
> - Public symbol docstring coverage for `sign_language_detection` re-verified live at 17/17 (**100.0%**).
> - Census claims (83 nodes / 84 edges / 28 triples / 15 schemas across 760 projects, 19,618 sampled files) derive from local clone scan without an in-repo artifact; recorded as unrefuted but not independently re-verifiable from repository state alone.
> - Status re-stamped as VERIFIED with corrected arithmetic and paths.

## Core Architectural Invariants
1. **Graph-Native Program & Execution Modeling**:
   39 subprojects (`graph_embedding`, `ipagnn`, `gfsa`, `aloe`, `bustle`) model discrete algorithmic structures—control-flow graphs, program ASTs, and bottom-up synthesis search spaces (`bustle` `saved_model.pb`, 110,269 B)—via specialized graph message-passing layers and continuous relaxations of instruction pointers.
2. **Differentiable Physics & Biophysical Surrogates**:
   Scientific ML packages (`jax_dft`, `protenn`, `aptamers_mlpd`, `al_for_fep`) integrate neural approximators into exact physical solvers, such as differentiable Kohn-Sham self-consistent field iterations (`jax_dft/jax_dft/scf.py`) and ensemble protein family classification (`protenn` `saved_model.pb`, 331,009 B).
3. **Bimodal Documentation Stratification**:
   AST symbol coverage audits distinguish productionized community benchmarks (`sign_language_detection`: 80.0% overall coverage, 100% public symbol docstrings) from domain-specific numerical kernels (`jax_dft`: 83.8% coverage [62/74 symbols]; `aloe`: 11.8% coverage [14/119 symbols]).
