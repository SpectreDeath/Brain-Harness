# ScaNN: Three-Phase Vector Search, Anisotropic Quantization & SOAR

## Provenance
- **Upstream Repository**: `https://github.com/google-research/google-research` (`scann/`)
- **Papers**: `https://arxiv.org/abs/1908.10396` (ICML 2020), `https://arxiv.org/abs/2404.00774`
- **Surfaced By**: Ontology-Spider cross-project hub graph (`eli5_retrieval_large_lm depends_on_project scann`)

## Architectural Rules (`scann/docs/algorithms.md` & `scann/scann/scann_ops/py/scann_builder.py`)
1. **3-Phase Pipeline**:
   - **Partition**: Skip partitioning below 20k vectors; otherwise set `num_leaves ~ sqrt(n)` and optionally enable SOAR spillover (`soar_lambda`, `overretrieve_factor`) for dot-product MIPS.
   - **Score**: Prefer `score_ah(..., dimensions_per_block=2, hash_type="lut16")` above 20k vectors using `noise_shaping_threshold` (`anisotropic_quantization_threshold`) so codebook error along the query direction is penalized more heavily than orthogonal error.
   - **Rescore**: Always follow approximate AH scoring with exact float32/int8 reordering over `reordering_num_neighbors > k`.
2. **Constraint-Checked Builder**: `ScannBuilder` raises early when AVQ/SOAR are paired with incompatible non-dot-product metrics and computes `global_topn` eligibility automatically.

## Harness Relevance
- Guides hybrid retrieval scaling and rescoring budgets in Brain Harness `vector_index` / RAG subsystems.
