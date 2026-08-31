# Deterministic Pre-LLM Context Optimization (`ki_self_20260827_01`)

## Summary
Agent step execution loops (`StepExecutionEngine`) require deterministic context optimization before dispatching prompts to LLM backends. Raw file dumps and verbose tabular data quickly exhaust context windows and degrade model reasoning quality.

## Architectural Invariant
1. **Pass 1 (Whitespace & Indentation Compaction):** Normalizes redundant blank lines and trailing whitespace.
2. **Pass 2 (Structured Data / Tabular Truncation):** Summarizes massive JSON payloads and CSV tables exceeding configurable line thresholds.
3. **Pass 3 (Polyglot AST Skeletonization):** Converts full code bodies into signatures and docstrings via language-specific AST parsers (with regex fallbacks), preserving structural awareness while slashing token volume by 35%–60%.

## Provenance
- Verified across Architecture Deepening Review Cycle 10 and prompt pruning plugin syntheses.
- Integrated into `plugins/memory_and_epistemics/context_compiler/`.
