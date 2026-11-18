# ASPEST: Bridging Active Sample Acquisition & Selective Prediction

## Provenance
- **Upstream Repository**: `https://github.com/google-research/google-research` (`active_selective_prediction/`)
- **Paper**: `https://arxiv.org/abs/2304.03870`
- **Surfaced By**: Ontology-Spider `.dialog` query + uncertainty shift cross-linking

## Key Mechanisms (`active_selective_prediction/methods/aspest.py`)
1. **Checkpoint Ensemble Aggregation (`update_ensemble_state`)**: Accumulates softmax outputs across intermediate training checkpoints rather than relying on a single overconfident final checkpoint.
2. **Band-Gated Pseudo-Labeling (`construct_pseudo_labeled_set`)**: Selects target samples strictly inside `[lower_threshold, upper_threshold)` (excluding noisy low-confidence predictions and redundant already-certain samples) and trains via `KLDivergence` alongside balanced `lambda * source_loss`.
3. **Budgeted Active Acquisition (`active_learning`)**: Allocates per-round oracle query quotas via `AverageMarginSampling` weighted by checkpoint-ensemble agreement before computing selective risk metrics.

## Harness Relevance
- Direct methodological pattern for `uncertainty_guard` abstention gating and targeted human-in-the-loop escalation when OOD inputs shift away from calibration priors.
