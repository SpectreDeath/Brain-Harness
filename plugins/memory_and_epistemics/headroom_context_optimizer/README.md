# Headroom Context Optimizer Plugin

The `plugin.headroom_context_optimizer` provides dynamic, content-aware context reduction, Cross-Context Retrieval (CCR) deduplication, prompt cache drift detection, and prior-turn extended thinking compaction directly within the Brain Harness agent step loop.

---

## Capabilities & Architecture

1. **ContentRouter & SmartCrusher**: Analyzes content format (JSON arrays, code, build/test logs, git diffs, search results) and selects format-specialized compression routines rather than lossy blind summarization.
2. **Cross-Context Retrieval (CCR)**: Replaces repeating multi-turn tool observations with short cryptographic digest markers (`[CCR tool digest: <hash> ... ]`) to reclaim thousands of tokens across multi-turn reasoning trajectories.
3. **Cache Alignment Detector**: Scans system prompts for volatile UUIDs, timestamps, hashes, and JWT tokens that invalidate Anthropic/OpenAI prompt cache prefixes, keeping cache hit rates high.
4. **Thinking Compaction**: Reclaims tokens from prior-turn extended reasoning `<thinking>` blocks to terminate recursive billing overhead.

---

## Tools & Entrypoints

| Tool Name | Description | Key Parameters |
| --- | --- | --- |
| `headroom_compress_content` | Route and compress arbitrary content based on syntax | `content`, `content_type`, `target_ratio`, `preserve_keys` |
| `headroom_dedup_turns` | Deduplicate repeating tool returns across turns with CCR markers | `messages`, `min_lines`, `min_chars` |
| `headroom_detect_cache_drift` | Structural detector for volatile prompt elements | `system_prompt` |
| `headroom_compact_thinking` | Compact prior-turn reasoning blocks into short digest markers | `messages`, `keep_last_turns` |
| `headroom_savings_metrics` | Retrieve real-time session token and cost reduction metrics | `reset` |

---

## Usage Example

```python
from harness.kernel.context import ServiceContext
from harness.services.headroom_optimizer import (
    HEADROOM_CONTEXT_OPTIMIZER_KEY,
    HeadroomContextOptimizerService,
)

# Resolve service from container
ctx = ServiceContext()
optimizer: HeadroomContextOptimizerService = ctx.require(HEADROOM_CONTEXT_OPTIMIZER_KEY)

# Compress large JSON array
result = optimizer.compress_content(
    content='[{"id": 1, "status": "active"}, {"id": 2, "status": "active"}]',
    content_type="json",
)
print(f"Compressed tokens: {result.compressed_tokens} ({result.savings_ratio * 100:.1f}% saved)")
```
