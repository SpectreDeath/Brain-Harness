# Google Research `smart_eval`: Sentence-Level Soft-LCS & Source-Augmented Evaluation

## 1. Context & Provenance

- **Upstream Repository**: `https://github.com/google-research/google-research` (`smart_eval/` subproject, 10 files)
- **Snapshot Reference**: `google-research-master` (archive snapshot, non-git)
- **Publication**: *SMART: Sentences as Basic Units for Text Evaluation* (`https://arxiv.org/abs/2208.01030`)
- **Primary Verified Sources**:
  - `smart_eval/README.md` (`L1-L36`)
  - `smart_eval/scorer.py` (`L27-L422`, sha256 `c8934c6e38d6b21b3c2282922dc87c70857973c03eb96f6b387a2ce8fdbfb67f`)
  - `smart_eval/matching_functions.py` (`L29-L124`, sha256 `510858484a7748b603d57f9e49f3cfd03a141fc6ba5f83315a5bd8c29cea58f8`)
  - `smart_eval/aggregate_functions.py` (`L24-L59`, sha256 `c5d39a1a0b9871b21d8b41b302c7c37c61392381c4620d38271560122864f2d8`)

---

## 2. Core Problem & Architectural Thesis

Token-level n-gram metrics (ROUGE/BLEU) miss lexical paraphrase equivalence and sentence-order faithfulness in summarization. `smart_eval` elevates sentences to the atomic unit, decouples pairwise sentence similarity scoring (`MatchingFunction`) from reduction (`AggregateFunction`), computes unigram, bigram, and soft longest-common-subsequence (`_soft_lcs`) alignments, and supports source-augmented evaluation (`max(reference_score, source_score)`).

---

## 3. Verified Implementation Invariants

### A. SMART-1 / SMART-2 / SMART-L Scoring (`scorer.py` `L27-L243`)
- `_smart_1` (`L86-L104`) takes row-wise `np.max` over reference and reversed candidate matrices before calling `aggregate_fn` to derive recall, precision, and harmonic `fmeasure`.
- `_smart_2` (`L106-L130`) pads both `score_matrix` and `rev_score_matrix` with zero sentinel borders (`[(1, 1), (1, 1)]`) and averages adjacent sentence pairs `(score_matrix[:-1, :-1] + score_matrix[1:, 1:]) / 2.0` so single-sentence summaries remain well-defined.
- `_soft_lcs` (`L148-L178`) runs dynamic programming matching `dp[i][j] = max(dp[i-1][j-1] + s, dp[i-1][j] + s, dp[i][j-1])`, allowing non-binary soft matches and multi-sentence consecutive alignments.
- `smart_score_precomputed` (`L180-L243`) raises `ValueError` if `is_symmetric_matching=False` without explicit `rev_ref_score_matrix` / `rev_src_score_matrix`, preventing silent transposition mistakes on directional model matchers (e.g. BLEURT/ANLI). When `source` is provided, it fuses scores via `max(ref_smart[x], src_smart[x])`.

### B. Pluggable Matching & Aggregation Abstractions (`matching_functions.py`, `aggregate_functions.py`)
- `MatchingFunction` (`L29-L124`) unifies single-string and batched list matching across `RougeMatchingFunction`, `MeteorMatchingFunction`, `ChrfMatchingFunction`, `BleuMatchingFunction`, and `BleurtMatchingFunction`.
- `AggregateFunction` (`L24-L59`) separates reduction policy (`MinAggregateFunction`, `MaxAggregateFunction`, `MeanAggregateFunction`, `WeightedMeanAggregateFunction` requiring explicit `'weights'`).

---

## 4. Applicability to Brain Harness & Anti-Patterns

- **Harness Seam Targets**: Evaluation suites and `UncertaintyGuard` (`src/harness/services/uncertainty_guard.py`) can adopt separated pairwise-similarity vs reduction contracts and explicit asymmetry guards (`is_symmetric_matching`) when scoring agent outputs against both prompts/sources and reference fixtures.
- **Anti-Patterns**:
  - **Do not transpose directional NLI/BLEURT score matrices implicitly** — require explicit reverse matrices whenever `is_symmetric_matching=False`.
  - **Do not fail on single-sentence summaries in bigram evaluators** — sentinel zero-padding keeps SMART-2 well-behaved across edge lengths.
