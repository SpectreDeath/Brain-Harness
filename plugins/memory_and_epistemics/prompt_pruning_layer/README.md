# domain.prompt_pruning_layer (v1.0.0)

Deterministic 3-pass prompt optimization engine (expired context elimination, duplicate passage reduction, and dependency restoration)

---

## Overview & Metadata

- **Plugin Directory**: `plugins/memory_and_epistemics/prompt_pruning_layer`
- **Isolation Mode**: `subprocess`
- **Services Provided**: None
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `prune_messages` | `(messages, assemble_prompt)` | Run all 3 deterministic optimization passes over prompt messages before model dispatch |
| `build_prompt` | `(messages)` | Format and assemble a list of messages into a single prompt string ordered by turn |
| `estimate_prompt_reduction` | `(messages)` | Calculate token counts before vs after 3-pass pruning with pass-by-pass removal diagnostics |
| `generate_benchmark_corpus` | `(num_turns, workload, seed)` | Generate a synthetic multi-turn dialogue corpus with controlled duplicates and tool usage |
| `benchmark_pruning_workloads` | `(num_turns, seed)` | Run comparative evaluation across chat, rag, and tool_agent workloads |

---

## Key Modules & AST Symbols

### Module [`main.py`](main.py)

Main entrypoint and typed tool registrations for Prompt Pruning Layer plugin.

#### Classes

- `class PromptPruningService`
  Service provider for deterministic prompt pruning.
  - `def prune(messages, assemble_prompt) -> dict[str, Any]`
  - `def build(messages) -> dict[str, Any]`
  - `def estimate(messages) -> dict[str, Any]`
  - `def benchmark(num_turns, seed) -> dict[str, Any]`


#### Functions

- `def prune_messages(messages, assemble_prompt) -> dict[str, Any]`
  - Run all 3 deterministic optimization passes over prompt messages before model dispatch.
- `def build_prompt(messages) -> dict[str, Any]`
  - Format and assemble a list of messages into a single prompt string ordered by turn.
- `def estimate_prompt_reduction(messages) -> dict[str, Any]`
  - Calculate token counts before vs after 3-pass pruning with pass-by-pass removal diagnostics.
- `def generate_benchmark_corpus(num_turns, workload, seed) -> dict[str, Any]`
  - Generate a synthetic multi-turn dialogue corpus with controlled duplicates and tool usage.
- `def benchmark_pruning_workloads(num_turns, seed) -> dict[str, Any]`
  - Run comparative evaluation across chat, rag, and tool_agent workloads.


### Module [`pruner_core.py`](pruner_core.py)

Core Prompt-Pruning Layer: Message models, 3-pass deterministic optimizer, and prompt builder.

#### Classes

- `class Message`
  A single unit of prompt state.
  - `def references() -> list[str]`
  - `def approx_token_count() -> int`
  - `def to_dict() -> dict[str, Any]`
- `class PruneReport`
  - `def token_reduction_pct() -> float`
  - `def to_dict() -> dict[str, Any]`
- `class PromptPruner`
  Three deterministic compiler passes over prompt messages before assembly.
  - `def prune(messages) -> tuple[list[Message], PruneReport]`
- `class PromptBuilder`
  Assembles a final prompt string from a list of Messages in chronological order.
  - `def build(messages) -> str`
- `class WorkloadConfig`
- `class CorpusResult`


#### Functions

- `def generate_corpus(num_turns, workload, seed) -> CorpusResult`



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
