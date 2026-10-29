# Headroom Context Optimization Architecture

## Executive Summary

Headroom (v0.41.0) defines a production-grade context optimization architecture for high-token LLM workloads. Rather than applying lossy, generic natural language summarization across context windows, Headroom treats context as a multi-modal stream of structured data types (JSON arrays, code ASTs, git diffs, build/test logs, search outputs, and prompt cache hot zones) and applies specialized, deterministic compression algorithms to each format.

---

## Core Theorems & Invariants

### 1. Syntactic Content Routing (ContentRouter)
Standard LLM agent context is dominated by high-volume tool observations: JSON query results, file reads, grep matches, and stack traces. A uniform compression strategy fails because:
* Summarizing JSON arrays causes hallucination of non-existent fields and schema distortion.
* Truncating code destroys matching bracket pairs and indentation levels.
* Truncating logs discards the root-cause traceback while retaining noisy setup lines.

`ContentRouter` dynamically detects payload formats via lexical and structural heuristics and routes to format-specialized transforms:
* **SmartCrusher**: Compresses repetitive JSON array records into unified schema key manifests with head/tail representative samples.
* **LogCompressor**: Retains the head (environment/command context) and tail (root-cause assertion/traceback) while omitting the noisy middle.
* **SearchCompressor**: Deduplicates common parent file paths across ripgrep outputs.
* **CodeCompressor**: Collapses redundant blank lines and trailing whitespace without touching AST indentation.

### 2. Cross-Context Retrieval (CCR) Deduplication
In autonomous ReAct agent loops, tools are frequently re-executed across turns (e.g., repeating `list_dir`, reading the same config file, or repeating test suite commands). This leads to massive quadratic context growth.

CCR computes a short 12-character SHA-256 block digest for every multi-line tool observation ($\ge 3$ lines, $\ge 40$ chars). If an identical observation block has already been recorded in a prior turn, CCR replaces the duplicate with a lightweight sentinel:
`[CCR tool digest: <hash> | original length: <N> chars | matching turn <origin>]`

This guarantees positive net savings while preserving full referential integrity for the agent.

### 3. Detector-Only Cache Hot Zone Alignment
Modern frontier models (Anthropic Claude, OpenAI GPT-4o, Gemini) utilize prompt prefix caching, providing 50% to 90% latency and cost discounts on cache hits. However, prompt caching requires byte-exact prefix stability.

A common anti-pattern is attempting to "clean" the system prompt by stripping dynamic timestamps or UUIDs in place. Headroom invariant PR-A2 proves that mutating the system prompt in place invalidates the cache hot zone. `CacheAligner` operates in **detector-only** mode: it structurally parses the system prompt for UUIDs, ISO-8601 timestamps, JWT tokens, and hex hashes, surfacing actionable warnings to developers without ever modifying prompt bytes.

### 4. Extended Thinking Token Compaction
On models supporting extended thinking (e.g., Claude 4.6+), prior-turn reasoning blocks (`<thinking>...</thinking>`) are sent back to the model as input tokens on subsequent turns and billed at standard input rates. In multi-turn trajectories, this compounding thinking overhead can account for over 40% of input token costs.

Headroom converts completed prior-turn thinking blocks into deterministic, memoized text markers (`[prior reasoning, compressed: <hash> (<N> toks)]`) while keeping the most recent active reasoning turns intact, terminating compounding billing without impairing reasoning continuity.

---

## Lineage & Provenance
* **Upstream**: Headroom Contributors (`D:/GitHub/cloned/headroom`, v0.41.0, Apache-2.0)
* **Synthesized In Harness**:
  * Service Protocol: `src/harness/services/headroom_optimizer.py`
  * Plugin Implementation: `plugins/memory_and_epistemics/headroom_context_optimizer/`
  * Agent Skill: `.agents/skills/headroom-context-optimizer/`
