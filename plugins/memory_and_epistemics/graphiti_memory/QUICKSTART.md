# Quickstart: `plugin.graphiti_memory`

The `plugin.graphiti_memory` plugin introduces temporal knowledge graph memory, bi-temporal fact invalidation, and tri-brid search to Brain Harness.

---

## 1. Standalone Tool Invocations

### Add an Episodic Turn
```python
from plugins.memory_and_epistemics.graphiti_memory import graphiti_add_episode

res = graphiti_add_episode(
    content="Alice lives in Berlin. Alice uses Python for data engineering.",
    group_id="agent_session_1",
    source_description="user_turn"
)
print("Episode UUID:", res["episode_uuid"])
print("Extracted entities:", res["extracted_entities"])
```

### Tri-brid Search & Reranking
```python
from plugins.memory_and_epistemics.graphiti_memory import graphiti_search

results = graphiti_search(
    query="Where does Alice live and what language does she use?",
    group_id="agent_session_1",
    limit=5
)
for fact in results["facts"]:
    print(f"[{fact['relation_name']}] {fact['fact']} (Score: {fact['score']})")
```

### Bi-Temporal Fact Invalidation
When facts evolve:
```python
# Ingest new contradicting fact
graphiti_add_episode(
    content="Alice moved to Tokyo.",
    group_id="agent_session_1"
)

# Active search automatically filters for current truth
current_res = graphiti_search("Where does Alice live?", group_id="agent_session_1")
print("Current truth:", current_res["facts"][0]["fact"])  # Alice moved to Tokyo

# Historical search includes invalidated facts
historical_res = graphiti_search("Where does Alice live?", group_id="agent_session_1", include_invalidated=True)
print("Historical facts count:", len(historical_res["facts"]))
```

---

## 2. Kernel Service Resolution

```python
from harness.kernel.context import ServiceContext
from harness.services.graphiti import GRAPHITI_MEMORY_KEY

async def my_agent_workflow(ctx: ServiceContext):
    memory_service = ctx.require(GRAPHITI_MEMORY_KEY)
    
    # Ingest turn
    await memory_service.add_episode("Project Athena depends on Redis.", group_id="prod")
    
    # Search
    search_res = await memory_service.search("What does Athena depend on?", group_id="prod")
    return search_res.facts
```
