# Memory Decay Engine Plugin — Quickstart Guide

The `domain.memory_decay_engine` plugin implements an Ebbinghaus Forgetting Curve memory management strategy with non-linear usage reinforcement.

## 🧠 Core Mathematics
- **Retention Score**:
  $$Ret = e^{-t / S}$$
  where $t$ is elapsed turns since last touch, and $S$ is stability.
- **Stability Reinforcement on Recall**:
  $$S_{new} = S_{old} \times (1 + \ln(1 + n))$$
  where $n$ is total recall count.
- **Eviction Rule**: When $Ret < 0.20$, the item is automatically pruned from the working set.

## 🚀 Quick Usage

```python
from plugins.memory_and_epistemics.memory_decay_engine.main import (
    memory_register, memory_recall, memory_step, memory_query_working_set
)

session = "agent_session_1"

# 1. Register foundational rule at turn 1
memory_register(session, "rule_python", "Use Python 3.10+ only", current_turn=1, is_foundational=True)

# 2. Spaced recalls at turn 5, 10, 20
for t in (5, 10, 20):
    memory_recall(session, "rule_python", current_turn=t)

# 3. Advance to turn 50 and step
memory_step(session, current_turn=50)

# 4. Check presence
ws = memory_query_working_set(session, current_turn=50)
print(f"Items in memory: {ws['working_set_size']}")
```
