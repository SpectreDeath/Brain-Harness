# Phase 4 — Next-5 Learning Targets Comparison

Evaluated **127** `grm` candidates (`has_tests=true, has_arxiv=true, harness_learned=false, is_generic_unit=false`).
Selection mode: `human_shortlists` (laptop-generated 8-item single-domain shortlists, seed `2026111841`, pure random draw; **not** the chat shortlists). Maximum possible `overlap@5` with `spider_composite`: **2** (not 5).

## Spider Composite Top 5

| Rank | unit_id | Domain | Score | Gap | Fan-In | Tests | Py Files |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `poem` | `vision_and_3d_project` | 0.6244 | 158.0 | 0 | 16 | 50 |
| 2 | `tunas` | `vision_and_3d_project` | 0.5981 | 158.0 | 0 | 16 | 40 |
| 3 | `t5_closed_book_qa` | `nlp_and_llm_project` | 0.5191 | 77.0 | 1 | 4 | 8 |
| 4 | `saccader` | `vision_and_3d_project` | 0.5163 | 158.0 | 0 | 11 | 27 |
| 5 | `tf3d` | `vision_and_3d_project` | 0.5104 | 158.0 | 0 | 9 | 32 |

## Method Comparison vs Blind Picks

| Method | Overlap@5 w/ Human (Ceiling) | Distinct Domains | Sum `domain_gap` | Picks |
|---|---:|---:|---:|---|
| `spider_composite` | 0 (ceiling: 2) | 2 | 709.00 | `poem`, `tunas`, `t5_closed_book_qa`, `saccader`, `tf3d` |
| `largest_5` | 0 | 4 | 297.12 | `abstract_nas`, `task_set`, `poem`, `symbolic_functionals`, `ravens` |
| `most_tests_5` | 0 | 3 | 281.38 | `task_set`, `neural_guided_symbolic_regression`, `symbolic_functionals`, `automl_zero`, `poem` |
| `random_5` | 1 | 3 | 288.12 | `task_set`, `robust_retrieval`, `structformer`, `dp_sgd_clipping`, `grow_bert` |
| `human_picks` | 5 | 5 | 350.12 | `dp_sgd_clipping`, `smart_eval`, `perturbations`, `norml`, `psycholab` |

## Methodology, Overlap Ceiling & Provenance Notes (Corrected 2026-11-19)

- **Overlap ceiling = 2 (not 5):** Of the 5 `spider_composite` top-5 targets (`poem`, `tunas`, `t5_closed_book_qa`, `saccader`, `tf3d`), only **`poem`** and **`saccader`** appeared in the regenerated 8-item shortlists; `tunas`, `t5_closed_book_qa`, and `tf3d` were never available to pick. Reported `overlap@5 = 0` must therefore be read against a ceiling of `2`.
- **Gap-sum structural asymmetry (`709.00` vs `350.12`):** `human_picks` were constrained to `1` pick per domain across `5` domains, whereas `spider_composite` placed `4/5` picks in the highest-gap domain (`vision_and_3d_project`, `gap=158.0`), structurally inflating the composite raw gap sum relative to a 1-per-domain pick set.
- **Provenance (`unconfirmed — no transcript in-repo`, recorded 2026-11-19):** The recorded picks (`dp_sgd_clipping`, `smart_eval`, `perturbations`, `norml`, `psycholab`) came from laptop-generated 8-item single-domain shortlists (seed `2026111841`, pure random draw, no top-score seeding), **not** from the 5 themed 6-item top-2-seeded shortlists delivered in chat. Four domains (`graph_and_program_project`, `privacy_fairness_safety_project`, `science_and_bio_project`, `speech_and_audio_project`) received no shortlist.
