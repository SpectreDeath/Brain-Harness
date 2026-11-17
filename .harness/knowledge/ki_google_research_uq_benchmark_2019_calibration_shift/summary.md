# Google Research `uq_benchmark_2019`: Predictive Uncertainty Under Dataset Shift

## 1. Context & Provenance

- **Upstream Repository**: `https://github.com/google-research/google-research` (`uq_benchmark_2019/`)
- **Snapshot Reference**: `google-research-master` (archive snapshot, non-git)
- **Publication**: *Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty Under Dataset Shift* (`https://arxiv.org/abs/1906.02530`)
- **Primary Verified Sources**:
  - `uq_benchmark_2019/README.md` (`L5-L33`)
  - `uq_benchmark_2019/metrics_lib.py` (`L30-L391`, sha256 `d8a27d5c62eb04f0d6396ea8326ece44c2f3b41f1503182451a64aede67247f2`)
  - `uq_benchmark_2019/calibration_lib.py` (`L30-L78`, sha256 `67a4be866f682fedd56262e2356343c06fd8df071a83837000dac14938c7d164`)

## 2. Core Architectural & Empirical Findings

1. **Post-Hoc Calibration Breaks Under Shift**: Across corrupted/shifted benchmarks (`MNIST` rotated, `CIFAR-10-C`, `ImageNet-C`, corrupted `Criteo`, `20 Newsgroups` + `LM1B`), in-distribution temperature scaling improves in-domain ECE yet degrades under shift, whereas deep ensembles / multi-sample marginalization maintain stronger shift calibration.
2. **Brier Decomposition (`metrics_lib.py`, `L319-L353`)**: `brier_decomposition()` separates overall error into:
   - `uncertainty` (intrinsic label-distribution entropy),
   - `resolution` (discriminative separation across predicted confidences), and
   - `reliability` (bin calibration mismatch).
   Temperature scaling alters `reliability` while leaving confidence `resolution` largely untouched — explaining the empirical observation also seen in `cisc` (`arXiv:2502.06233`).
3. **Selective Abstention Sweeps (`L189-L215`)**: `compute_accuracies_at_confidences(labels, probs, thresholds)` tracks `(accuracy, coverage_count)` at monotonic confidence thresholds `T`, letting gating layers measure risk-coverage tradeoffs directly.
4. **Numerical Boundary Guard (`L64-L66`)**: Exact `0.0` probabilities are clamped to `1e-8` prior to `np.digitize(..., right=True)` so lower-bound edge predictions stay inside the first bin.

## 3. Applicability to Brain Harness

- Pair `compute_accuracies_at_confidences` threshold sweeps with `UncertaintyGuard` gating thresholds (`0.60` / confidence cutoffs) so confidence gates are calibrated on risk-coverage curves rather than global ECE alone.
- Prefer ensemble / multi-sample trace aggregation (`cisc`) over single-sample post-hoc logit temperature scaling when operating across novel or shifted domains.
