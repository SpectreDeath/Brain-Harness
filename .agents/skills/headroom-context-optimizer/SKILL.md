---
name: headroom-context-optimizer
description: Optimize LLM context budgets, compress tool observations, deduplicate multi-turn transcripts, and detect prompt cache drift. Do not use for raw model prompt drafting or simple file truncation.
---

# Headroom Context Optimizer: Production Context Engineering

`headroom-context-optimizer` provides automated, structure-aware context optimization, Cross-Context Retrieval (CCR) deduplication, prompt cache drift detection, and prior-turn extended thinking compaction. It is modeled after the industrial patterns in Headroom v0.41.0 to slash token consumption by 50% to 90% without losing reasoning fidelity.

See [CARD.md](CARD.md) for the companion summary card, 5-stage progression matrix, and invariants checklist.

---

## The 5-Stage Context Optimization Pipeline

```text
[1. Trigger & Type Detection] ──► [2. ContentRouter & SmartCrush] ──► [3. CCR Cross-Turn Dedup]
                                                                                │
                                                                                ▼
[5. Savings Ledger & Attribution] ◄── [4. Cache Alignment Check] ◄──────────────┘
```

---

## 1. Trigger & Type Detection

Evaluate candidate content or conversation transcripts against optimization thresholds:

1. **Detect Structure**:
   - Inspect payloads to identify format: `json` (arrays/objects), `code` (Python, JS, TS, Rust), `diff` (git patches), `log` (build/test traces), `search` (grep/ripgrep matches), or `text`.
2. **Apply Activation Gates**:
   - Only compress content exceeding 100 characters or 25 tokens.
   - For multi-turn transcripts, gate deduplication on messages exceeding 3 lines and 40 characters.

> **Completion criterion**: Content format classified and activation threshold verified.

---

## 2. ContentRouter & SmartCrush

Route content to specialized compressors rather than uniform blind summarization:

1. **JSON Array Compaction (SmartCrusher)**:
   - For lists with >5 dict elements, extract unified schema keys, retain a 3-row head sample and 2-row tail sample, and emit a compact summary structure.
2. **Code AST-Aware Compression**:
   - Strip redundant whitespace and consecutive blank lines while preserving AST boundaries.
3. **Log & Search Reduction**:
   - Truncate repetitive log entries, keeping the initial 10 lines, omitted count sentinel, and trailing 10 lines.

> **Completion criterion**: Structure-aware compression applied; savings ratio $\ge 0.20$ on redundant data.

---

## 3. CCR Cross-Turn Deduplication

Reclaim context from repetitive multi-turn tool observations:

1. **Compute SHA-256 Block Digest**:
   - Calculate short 12-character cryptographic digests for multi-line assistant and tool returns.
2. **Emit CCR Retrieval Marker**:
   - Replace repeating observation blocks with `[CCR tool digest: <hash> | original length: <N> chars | matching turn <origin>]`.
3. **Preserve Recent Turns**:
   - Keep the most recent 2 to 4 turns completely verbatim for immediate reasoning coherence.

> **Completion criterion**: Duplicate tool returns folded into deterministic retrieval markers.

---

## 4. Cache Alignment Check

Inspect system prompts to guarantee stable prefix prompt caching:

1. **Scan for Volatile Elements**:
   - Check system prompt for UUIDs, ISO-8601 timestamps, JWT tokens, and hex hashes.
2. **Enforce Prompt Immutability (Detector-Only)**:
   - Never mutate system prompts in place (which destroys cache prefixes).
   - Flag detected volatile elements to the developer so dynamic context can be relocated into user turns.

> **Completion criterion**: System prompt confirmed 100% byte-stable or volatile elements flagged.

---

## 5. Savings Ledger & Attribution

Record cumulative context savings:

1. **Calculate Metrics**:
   - Track `total_in_tokens`, `total_out_tokens`, `net_tokens_saved`, and estimated dollar savings ($3.00/MTok blend).
2. **Emit Observability Event**:
   - Log savings metrics into the session transcript or Prometheus `/metrics`.

> **Completion criterion**: Savings ledger updated and compression statistics surfaced.

---

## Anti-Patterns

- **Uniform Blind Truncation** — Chopping raw characters off the end of a payload without recognizing JSON, code, or log structures.
- **System Prompt Cache Busting** — Dynamically inserting timestamps or run IDs into the system prompt, invalidating Anthropic/OpenAI prompt cache prefixes.
- **Excessive Dedup Fragmentation** — Folding small single-line strings into digest markers where the marker itself costs more tokens than the original text.
- **LLM Parse Failure Reprompts** — Paying full LLM API roundtrips for malformed JSON before executing fast local string salvage.
- **Unverified In-Process Sandboxing** — Running untrusted external scripts in-process without sandboxed execution boundaries.
