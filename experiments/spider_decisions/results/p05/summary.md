# Phase 5 — Entropy-Driven Question Selection vs Random

Simulated hidden-target narrowing across the top **20** candidates from Phase 4.

## Policy Comparison

| Policy | Mean Questions | Max Questions | Uniquely Identified |
|---|---:|---:|---:|
| `entropy` (`classification_score`) | 1.80 | 2 | 20/20 (100.0%) |
| `random` (seed `20261118 + i`) | 3.65 | 7 | 20/20 (100.0%) |

## Per-Target Breakdown

| # | unit_id | Entropy Qs | Entropy Unique | Random Qs | Random Unique |
|---:|---|---:|---|---:|---|
| 1 | `poem` | 2 | True | 4 | True |
| 2 | `tunas` | 2 | True | 4 | True |
| 3 | `t5_closed_book_qa` | 2 | True | 4 | True |
| 4 | `saccader` | 1 | True | 5 | True |
| 5 | `tf3d` | 1 | True | 2 | True |
| 6 | `uflow` | 2 | True | 4 | True |
| 7 | `study_recommend` | 1 | True | 1 | True |
| 8 | `smerf` | 2 | True | 2 | True |
| 9 | `factors_of_influence` | 2 | True | 4 | True |
| 10 | `autoregressive_diffusion` | 2 | True | 2 | True |
| 11 | `robust_loss` | 2 | True | 4 | True |
| 12 | `clip_as_rnn` | 2 | True | 2 | True |
| 13 | `correct_batch_effects_wdn` | 2 | True | 2 | True |
| 14 | `stable_transfer` | 2 | True | 6 | True |
| 15 | `video_structure` | 2 | True | 4 | True |
| 16 | `robust_loss_jax` | 2 | True | 2 | True |
| 17 | `flare_removal` | 2 | True | 5 | True |
| 18 | `factorize_a_city` | 2 | True | 6 | True |
| 19 | `smug_saliency` | 2 | True | 7 | True |
| 20 | `task_set` | 1 | True | 3 | True |
