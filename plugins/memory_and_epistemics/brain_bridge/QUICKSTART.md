# Quickstart: `plugin.brain_bridge`

Federate and query external agent brains, IDE transcripts, and knowledge libraries on demand via directory path.

---

## 1. Attach an External Brain

Mount an Antigravity IDE brain directory or another repository's memory store:

```python
from plugins.memory_and_epistemics.brain_bridge.main import brain_attach

# Mount Antigravity Brain
res = brain_attach(
    folder_path=r"C:\Users\spectre\.gemini\antigravity-ide\brain",
    alias="antigravity_core",
    read_transcripts=True,
    attach_mode="lens",
)
print(res)
```

## 2. Query Across Attached Brains

Perform semantic cosine similarity queries across indexed documents and past execution transcripts:

```python
from plugins.memory_and_epistemics.brain_bridge.main import brain_query

results = brain_query(
    query="How were service keys and topological sorting implemented in plugins?",
    brain_alias="antigravity_core",
    include_trajectories=True,
    top_k=5,
)
for r in results["results"]:
    print(f"[{r['score']}] ({r['type']}) {r['file']}: {r['snippet'][:120]}...")
```

## 3. Inspect Mounted Brains

```python
from plugins.memory_and_epistemics.brain_bridge.main import brain_list_attached

attached = brain_list_attached()
print(f"Total brains mounted: {attached['attached_count']}")
```

## 4. Detach a Brain

```python
from plugins.memory_and_epistemics.brain_bridge.main import brain_detach

brain_detach("antigravity_core")
```
