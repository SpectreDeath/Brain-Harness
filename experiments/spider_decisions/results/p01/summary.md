# Phase 1 — False-Bridge Audit & Fix Summary

## Before vs After Metrics

| Metric | Before Fix | After Fix |
|---|---:|---:|
| Total bridges | 40 | 32 |
| True positives | 33 | 32 |
| False positives | 7 | 0 |
| FP rate | 0.1750 | 0.0000 |
| True-bridge recall | 1.0000 | 0.9697 |
| `airllm_plus/runtime` gone | False | True |
| `grm/rpc` gone | False | True |

## Bridge Changes
- **Removed FPs (7):** grm/rpc -> ki_20260831_openclaw_02, gvisor/governance -> ki_responsible_ai_prototyping, gvisor/shim -> ki_shim_bounded_session_and_layered_skill_loader, gvisor/tools -> ki_20260830_grok_01, airllm/data -> ki_solla_dikw_data_asset_continuum, airllm/eval -> ki_rea_sig_anthea_eval_1f061854, airllm_plus/runtime -> ki_agent_reach_layered_backend_fallback
- **Removed TPs (1):** grm/aloe -> ki_20261110_google_research_gnn_and_scientific_ml
- **Remaining FPs (0):** none

## Regression Set Verification (Step 1.8)

| Snapshot | Unit | Status | Match Strength | Learned KI ID |
|---|---|---|---|---|
| google_portfolio_root | gvisor | PASS | structured | `ki_google_gvisor_sentry_gofer_sandbox` |
| grm | latent_programmer | PASS | structured | `ki_google_research_latent_programmer_vqvae` |
| grm | active_selective_prediction | PASS | structured | `ki_google_research_aspest_active_selective_prediction` |
| grm | scann | PASS | structured | `ki_google_research_scann_anisotropic_vq` |
| grm | cisc | PASS | structured | `ki_google_research_cisc_confidence_voting` |
| grm | gfsa | PASS | structured | `ki_google_research_gfsa_automaton_layer` |
| grm | etcmodel | PASS | structured | `ki_google_research_etcmodel_long_structured_attention` |
| grm | imp | PASS | structured | `ki_google_research_imp_multimodal_config_registry` |
| grm | uq_benchmark_2019 | PASS | structured | `ki_google_research_uq_benchmark_2019_calibration_shift` |
| airllm | air_llm | PASS | structured | `ki_airllm_layerwise_streaming_and_moe_expert_offload` |
