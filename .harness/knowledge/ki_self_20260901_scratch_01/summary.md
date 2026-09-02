# Burrows' Delta Stylometry & Corpus Normalization

## Metadata
- **KI ID**: `ki_self_20260901_scratch_01`
- **Source Target**: `C:\Users\spectre\.gemini\antigravity-ide\scratch`
- **Format**: `python_nlp_stylometry_script`
- **Timestamp**: `2026-09-01T18:45:00Z`
- **Status**: `VERIFIED`

## Distilled Learning
# KI: Burrows' Delta Stylometry & Corpus Normalization

## Operational Summary
Computational authorship attribution packages (`faststylometry`) calculate delta z-score distance matrices across document frequency distributions. The underlying `calculate_burrows_delta` algorithm requires:
1. `train_corpus` and `test_corpus` to contain tokenized book representations (`corpus.tokenise(tokenise_remove_pronouns_en)`).
2. Non-zero token length across both corpora (`len(corpus.tokens) > 0`).

When loading documents from nested directory trees or flat folder layouts, default library loaders often fail if the directory layout does not match rigid expected subfolder conventions. Implementing an explicit normalizer that:
- Recursively traverses folders for `.txt` files.
- Parses metadata splits from filenames (`Author - Title.txt` or `Author.txt`).
- Adds individual texts via `Corpus.add_book(author, title, text)`.
- Explicitly asserts `len(train_corpus.tokens) > 0` and `len(test_corpus.tokens) > 0` before delta calculation.
guarantees robust, zero-crash forensic stylometry analysis across heterogeneous text corpuses.

## Invariant Rule
Always normalize document filenames and assert non-zero token length across train and test corpora before executing statistical delta distance matrix calculations.

## Primary Lineage
- **Assertion**: faststylometry requires strict multi-book tokenization prior to vocabulary calculation; walking unstructured directory layouts where file naming diverges from 'Author - Title.txt' results in empty corpus token arrays and fatal assertion errors. Explicit folder recursive traversal and metadata normalization bridges disparate document collections into standardized Pandas distance matrices.
  - `primary_code`: `C:/Users/spectre/.gemini/antigravity-ide/scratch/tools_faststylometry.py#L1-L45` (Verified: True)
  - `primary_code`: `C:/Users/spectre/.gemini/antigravity-ide/scratch/diagnose_corpus.py#L1-L25` (Verified: True)
  - `visual_brief`: `C:/Users/spectre/AppData/Local/Temp/harness-reflection-scratch-20260901-184500.html` (Verified: True)
