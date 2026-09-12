# domain.agent_supervisor (v1.0.0)

Hierarchical multi-agent supervisor, token budget allocator, and consensus voting orchestrator

---

## Overview & Metadata

- **Plugin Directory**: `plugins/agent_orchestration/agent_supervisor`
- **Isolation Mode**: `in_process`
- **Services Provided**: None
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `coordinate_swarm_tasks` | `(objective, agents, max_total_tokens)` | Decompose a swarm objective into worker agent assignments with assigned token budgets and roles |
| `tally_consensus_votes` | `(votes, threshold)` | Aggregate and tally multi-agent votes on proposals with configurable quorum and consensus threshold |

---

## Key Modules & AST Symbols

### Module [`main.py`](main.py)

Hierarchical multi-agent supervisor, token budget allocator, and consensus voting plugin.

#### Functions

- `def coordinate_swarm_tasks(objective, agents, max_total_tokens) -> dict[str, Any]`
  - Divide a swarm objective across specialized worker agents with token allocations.
- `def tally_consensus_votes(votes, threshold) -> dict[str, Any]`
  - Tally agent votes to determine if supermajority consensus is reached.



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
