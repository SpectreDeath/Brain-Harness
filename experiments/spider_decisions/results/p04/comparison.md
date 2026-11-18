# Phase 4 — Next-5 Learning Targets Comparison

Evaluated **127** `grm` candidates (`has_tests=true, has_arxiv=true, harness_learned=false, is_generic_unit=false`).

## Spider Composite Top 5

| Rank | unit_id | Domain | Score | Gap | Fan-In | Tests | Py Files |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `poem` | `vision_and_3d_project` | 0.6244 | 158.0 | 0 | 16 | 50 |
| 2 | `tunas` | `vision_and_3d_project` | 0.5981 | 158.0 | 0 | 16 | 40 |
| 3 | `t5_closed_book_qa` | `nlp_and_llm_project` | 0.5191 | 77.0 | 1 | 4 | 8 |
| 4 | `saccader` | `vision_and_3d_project` | 0.5163 | 158.0 | 0 | 11 | 27 |
| 5 | `tf3d` | `vision_and_3d_project` | 0.5104 | 158.0 | 0 | 9 | 32 |

## Method Comparison vs Blind Picks

| Method | Overlap@5 w/ Human | Distinct Domains | Sum `domain_gap` | Picks |
|---|---:|---:|---:|---|
| `spider_composite` | 0 | 2 | 709.00 | `poem`, `tunas`, `t5_closed_book_qa`, `saccader`, `tf3d` |
| `largest_5` | 0 | 4 | 297.12 | `abstract_nas`, `task_set`, `poem`, `symbolic_functionals`, `ravens` |
| `most_tests_5` | 0 | 3 | 281.38 | `task_set`, `neural_guided_symbolic_regression`, `symbolic_functionals`, `automl_zero`, `poem` |
| `random_5` | 0 | 3 | 288.12 | `task_set`, `robust_retrieval`, `structformer`, `dp_sgd_clipping`, `grow_bert` |
| `human_picks` | 5 | 4 | 191.25 | `cfq_pt_vs_sa`, `factoring_sqif`, `learnreg`, `mpi_extrapolation`, `storm_optimizer` |
