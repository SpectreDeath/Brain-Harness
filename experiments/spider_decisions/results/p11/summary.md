# Phase 11 — Evidence-Grounded CISC Swarm Voting Summary

Evaluated **12** disputes (`verified=1.0x`, `unverified=0.6x`, `no KI=0.4x`) using `ConsensusEngine.evaluate_cisc_consensus(..., normalization='softmax', temperature=2.5)`.

## Headline Metrics

| Metric | Value |
|---|---:|
| Raw CISC accuracy | 2/12 (16.7%) |
| Evidence-grounded accuracy | 11/12 (91.7%) |
| Total winner flips | 9 |
| Flips toward **correct** (verified KI) | 9 |
| Flips toward **incorrect** | 0 |

## Per-Dispute Breakdown

| # | Topic | Raw Winner | Grounded Winner | Correct Choice | Flipped | Grounded OK |
|---:|---|---|---|---|---|---|
| 1 | Vector index asymmetric rescoring budget | `arrow_mmap_flat_scan` (`False`) | `scann_anisotropic_rescore` | `scann_anisotropic_rescore` | True | True |
| 2 | Uncertainty guard OOD human escalation gate | `three_layer_heuristics` (`False`) | `aspest_band_escalation` | `aspest_band_escalation` | True | True |
| 3 | Swarm multi-trace confidence aggregation strategy | `unweighted_majority` (`False`) | `cisc_softmax_wqd` | `cisc_softmax_wqd` | True | True |
| 4 | Distribution-shift calibration evaluation metric | `single_static_threshold` (`False`) | `selectivity_sweep_brier` | `selectivity_sweep_brier` | True | True |
| 5 | Lazily-staged plugin disk artifact cache policy | `xxhash_arrow_stream` (`False`) | `superblock_dual_lru` | `superblock_dual_lru` | True | True |
| 6 | MoE layer offloading pinned host buffer bound | `unbounded_pin_all` (`False`) | `mxfp4_capped_pinned_2gib` | `mxfp4_capped_pinned_2gib` | True | True |
| 7 | Untrusted external plugin filesystem isolation | `ad_hoc_runner_env` (`False`) | `gvisor_sentry_gofer_fd` | `gvisor_sentry_gofer_fd` | True | True |
| 8 | Latent sequence pretraining bypass prevention | `direct_autoregressive` (`False`) | `vqvae_discrete_latent_plan` | `vqvae_discrete_latent_plan` | True | True |
| 9 | Structured long-context attention complexity routing | `complexity_tier_only` (`False`) | `etcmodel_global_local_attn` | `etcmodel_global_local_attn` | True | True |
| 10 | AST graph absorption linear solver layer (control) | `gfsa_richardson_absorption` (`True`) | `gfsa_richardson_absorption` | `gfsa_richardson_absorption` | False | True |
| 11 | Multimodal config override immutability (control) | `locked_dataclass_registry` (`True`) | `locked_dataclass_registry` | `locked_dataclass_registry` | False | True |
| 12 | Chunked vocab loss vs overwhelming unverified plurality (stress) | `full_logits_materialized` (`False`) | `full_logits_materialized` | `chunked_vocab_ce` | False | False |
