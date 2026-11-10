# Graph-Native Program Representations & Differentiable Scientific ML

## Context & Provenance
Synthesized from MemGraphRAG 3-layer ontology extraction (83 nodes, 84 edges, 28 fact triples, 15 schemas), REA SavedModel protobuf inspection, and `DocSynchronizerService` AST audits across `google-research-master`.

## Core Architectural Invariants
1. **Graph-Native Program & Execution Modeling**:
   39 subprojects (`graph_embedding`, `ipagnn`, `gfsa`, `aloe`, `bustle`) model discrete algorithmic structures—control-flow graphs, program ASTs, and bottom-up synthesis search spaces (`bustle` `saved_model.pb`, 110,269 B)—via specialized graph message-passing layers and continuous relaxations of instruction pointers.
2. **Differentiable Physics & Biophysical Surrogates**:
   Scientific ML packages (`jax_dft`, `protenn`, `aptamers_mlpd`, `al_for_fep`) integrate neural approximators into exact physical solvers, such as differentiable Kohn-Sham self-consistent field iterations (`jax_dft/scf.py`) and ensemble protein family classification (`protenn` `saved_model.pb`, 331,009 B).
3. **Bimodal Documentation Stratification**:
   AST symbol coverage audits distinguish productionized community benchmarks (`sign_language_detection`: 80.0% overall coverage, 100% public symbol docstrings) from domain-specific numerical kernels (`jax_dft`: 54.0% coverage; `aloe`: 7.2% coverage).
