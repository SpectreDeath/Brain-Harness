# Quick Start Guide: `domain.agent_supervisor` (v1.0.0)

> Hierarchical multi-agent supervisor, token budget allocator, and consensus voting orchestrator

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`coordinate_swarm_tasks`**: Decompose a swarm objective into worker agent assignments with assigned token budgets and roles
- **`tally_consensus_votes`**: Aggregate and tally multi-agent votes on proposals with configurable quorum and consensus threshold

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.agent_supervisor.coordinate_swarm_tasks', {'objective': '<objective>', 'agents': '<agents>', 'max_total_tokens': '<max_total_tokens>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.agent_supervisor
harness plugin enable domain.agent_supervisor
```

## ⚡ Available Entrypoints & Skills
- **`coordinate_swarm_tasks(objective: string, agents: array, max_total_tokens: integer)`**
  Decompose a swarm objective into worker agent assignments with assigned token budgets and roles
- **`tally_consensus_votes(votes: array, threshold: number)`**
  Aggregate and tally multi-agent votes on proposals with configurable quorum and consensus threshold