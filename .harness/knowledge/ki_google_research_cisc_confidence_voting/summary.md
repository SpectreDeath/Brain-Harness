# Google Research `cisc`: Confidence-Informed Self-Consistency & Within-Question Discrimination

## 1. Context & Provenance

- **Upstream Repository**: `https://github.com/google-research/google-research` (`cisc/` subproject, 38 files)
- **Snapshot Reference**: `google-research-master` (archive snapshot, non-git)
- **Publication**: *Confidence Improves Self-Consistency in LLMs* (ACL Findings 2025, `https://arxiv.org/abs/2502.06233`)
- **Authors**: Amir Taubenfeld\*, Tom Sheffer\*, Eran Ofek, Amir Feder, Ariel Goldstein, Zorik Gekhman, Gal Yona
- **Primary Verified Sources**:
  - `cisc/README.md` (`L182-L213`)
  - `cisc/src/confidence_extraction.py` (`L24-L106`, sha256 `83c2efec11bd43a37072509fde0073c85453bc21c872cf6ef9b4e133e670f8f4`)
  - `cisc/src/self_consistency.py` (`L28-L89`)
  - `cisc/src/post_processing/aggregators.py` (`L32-L188`, sha256 `785708c2801aa04fd83abb7bb29e2853cb8c9a013890a1fb6f407f0796f827dd`)
  - `cisc/src/post_processing/metrics_calculators.py` (`L26-L83`, sha256 `2ebb5289347aec3cec0b32a26c0d7c2c21b525dd3461542b791e9a0f4545e53c`)
  - `cisc/src/post_processing/calibration_util.py` (`L26-L115`, sha256 `2df30280e3965dd89b1d652a55313c02e4abcfbb995bd75937d99d20ad311e67`)
  - `cisc/src/post_processing/per_question_eval.py` (`L136-L235`)

---

## 2. Core Problem & Architectural Thesis

Standard self-consistency (`SC`) samples $m$ chain-of-thought traces and gives every trace equal weight ($1$) in majority voting. Per `cisc/README.md`, CISC augments each reasoning trace with a lightweight self-generated confidence estimate and performs confidence-weighted majority voting, reducing the number of sampled reasoning paths required for equivalent accuracy by **over 40% on average** across 9 models and 4 datasets (`bbh`, `gsm8k`, `math`, `mmlu_pro`; e.g., reaching 30-sample SC accuracy in 8 samples on Gemma2-9B / MATH).

A central empirical insight is that global calibration metrics such as Expected Calibration Error (`ECE`, implemented alongside Brier score and `TemperatureScaling` in `calibration_util.py`) poorly predict whether confidence weights improve per-question voting. Instead, CISC introduces **Within-Question Discrimination (WQD)**, measuring how reliably confidence scores rank correct traces above incorrect traces *within* the same prompt's candidate pool.

---

## 3. Verified Implementation Invariants

### A. Multi-Signal Confidence Extraction (`confidence_extraction.py` & `self_consistency.py`)
- `ConfidenceExtractionConfig` (`L24-L42`) extracts confidence deterministically using `temperature=0.0`, `num_tokens=10`, and `verbal_eos_pattern=")"` over explicit `confidence_options`.
- `ConfidenceExtractionType` (`L48-L97`) parameterizes five discrete elicitation formats (`BINARY` `[0, 1]`, `BINARY_FT` `["F", "T"]`, `BINARY_FT01` `["0", "1"]`, `BINARY_MP` `["-", "+"]`, `HUNDRED` `0..100`) plus `NONE`.
- `AggregatedConfidenceExtractionConfig` (`L99-L106`) decouples extraction into three orthogonal channels attached to each `SelfConsistencyResult.Trace`:
  1. `verbal_confidence` (`verbal_conf`)
  2. `confidence_likelihoods` (token likelihood distribution over option tokens, e.g., `logit_confidence` / `binary_confidence`)
  3. `run_sequence_probability` (`response_probability`)

### B. Temperature-Normalized Weighted Voting (`aggregators.py` & `per_question_eval.py`)
- `AggregatorConfig` (`L47-L90`, frozen dataclass) enforces `confidence_col_name` belongs to `['verbal_confidence', 'logit_confidence', 'response_probability', 'binary_confidence']` and selects across `AggregatorType` variants: `SC`, `CISC`, `TIE`, `MAX`, `ORACLE`, `ORACLE_BY_CONF`.
- `majority_with_conf(answers, confidences, norm_type=NormalizationType.LINEAR, temp=1.0, only_tie_break=False)` (`L105-L188`):
  1. Filters NaN/empty answers and `NaN` confidences while explicitly preserving valid `0` confidence values.
  2. Supports unweighted vote collection when `only_tie_break=True`, falling back to weighted sums only to resolve ties (`TIE` aggregator).
  3. Normalizes confidence weights using either `LINEAR` (`temp * (c - min) + 1`) or `SOFTMAX` (`util.softmax(confidences, temp)`, the paper's primary aggregator) rather than unbounded raw probabilities.
  4. Accumulates normalized weights per candidate answer via `Counter` and returns `(chosen_answer, chosen_weight_sum / sum(confidences))`.

### C. Trace-Savings & Discrimination Evaluation (`metrics_calculators.py` & `calibration_util.py`)
- `calculate_metrics_at_position(baseline, evaluated, evaluated_position)` (`L48-L83`) returns frozen `ResultMetrics` (`evaluated_position`, `baseline_accuracy`, `evaluated_accuracy`, `comparable_baseline_traces_needed`) across bootstrapped trace lengths `traces_lens` (`per_question_eval.py`) to directly measure sample-budget reduction against equal-weight `SC`.
- `calibration_util.py` separates global calibration (`compute_ece`, `compute_brier`, `TemperatureScaling`) from within-question ranking used by CISC voting.

---

## 4. Applicability to Brain Harness & Anti-Patterns

- **Harness Seam Targets**:
  - Multi-sample verification / `UncertaintyGuard` (`src/harness/services/uncertainty_guard.py`) and ensemble agent voting can replace equal-weight voting or single-trace sampling with temperature-scaled `SOFTMAX` weighting across verbal and log-probability confidence signals, while retaining `TIE` tie-breaking as a low-variance fallback.
  - Swarm deliberation pipelines can adopt per-question discrimination (WQD) and trace-savings metrics (`ResultMetrics`) when evaluating whether verifier confidence signals improve consensus over unweighted voting.
- **Anti-Patterns**:
  - **Do not drop `0`-confidence traces as missing** — filter strictly on `NaN`/empty values as in `majority_with_conf`.
  - **Do not optimize temperature solely for global ECE** — calibrate weight temperature (`NormalizationType.SOFTMAX`, `temp`) against within-question trace discrimination and downstream CISC voting accuracy.
  - **Do not rely on raw unnormalized weights** — linear or softmax normalization prevents extreme log-prob outliers from collapsing ensemble diversity into `MAX` selection unintentionally.
