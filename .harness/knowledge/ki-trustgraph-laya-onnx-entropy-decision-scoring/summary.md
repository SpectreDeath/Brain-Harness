# TrustGraph: Laya ONNX Decision Scoring & Entropy Confidence Calibration

## Overview
- **Source Repository**: `https://github.com/trustgraph-ai/trustgraph` (`17e5d742`)
- **Primary Files**:
  - `trustgraph-laya/trustgraph/model/decision_scoring/laya/engine.py#L1-L140`

## Core Architecture & Invariants
1. **Typed Decision Modes (`QTYPES`)**: Restricts scoring tasks to three discrete modes: `choice` (`0`), `score` (`1`), and `noul` (`2`), backed by `onnx-community/laya-multilingual-ONNX`.
2. **Temperature Hygiene & Bucketing (`_clamp_temperature`, `_temp_bucket`)**: Non-finite temperatures (`NaN`, `±Inf`) reset to `1.0`, and finite values clamp to `[TEMP_MIN=0.5, TEMP_MAX=5.0]` before bucket quantization.
3. **Normalized Shannon Entropy Confidence (`_confidence_from_probs`)**: For $k \ge 2$ candidate probabilities normalized over the simplex, confidence equals $1 - H(p) / \ln(k) \in [0, 1]$; degenerate cases ($k < 2$) return `1.0` deterministically without division-by-zero.
4. **Head-First Token Budgeting (`_build_sequence`)**: Enforces `max_len = 512` and `head_max_len = 192`. Option budget allocates `opt_budget = head_max_len - k * (1 + min(48, option_tokens_each))`, triggering per-option shrinkage warnings whenever `opt_budget < 16` so option labels never starve the question header.

## Decision Heuristics & Anti-Patterns
- **Never divide Shannon entropy by $\ln(k)$ without checking $k < 2$**: Guard degenerate single-option prompts upfront.
- **Never allow unbounded candidate option lists to truncate the question header**: Reserve `head_max_len = 192` tokens inside the 512-token sequence window and shrink per-option slices when `opt_budget < 16`.
