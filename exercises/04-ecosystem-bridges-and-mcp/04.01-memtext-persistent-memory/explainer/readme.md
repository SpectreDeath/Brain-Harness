# Memtext Persistent Memory Bridge

## Overview

The `MemtextServicePlugin` integrates persistent semantic memory, decision ledgers, and context offloading into Brain Harness through the `EcosystemBridgePlugin` base adapter.

```python
from harness.bridges.memtext import MEMORY_SERVICE_KEY, MemtextServicePlugin, MemtextService

# Load the bridge
bridge = MemtextServicePlugin()
await bridge.on_load(ctx)
await bridge.on_enable()

# Store and recall memories
mem: MemtextService = ctx.require(MEMORY_SERVICE_KEY)
await mem.remember("auth_token", "Bearer eyJhbGciOi...")
results = await mem.recall("auth_token")
```

## Key Capabilities

- **Context Offloading**: Offload bulky agent scratchpads to save active context window tokens.
- **Decision Audit Ledger**: Append immutable agent decision records with metadata.
- **Ecosystem Locator**: Automatically resolves neighbor repository paths (`MEMTEXT_PATH`).
