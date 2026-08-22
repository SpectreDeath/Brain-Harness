# Quickstart: `plugin.brain_bridge`

Federate and query external agent brains, Git repositories, IDE transcripts, and knowledge libraries on demand via directory path or remote Git URL.

---

## 1. Attach an External Brain or Repository

Mount a local folder, Git repository, or remote GitHub repository:

```python
from plugins.memory_and_epistemics.brain_bridge.main import brain_attach

# A. Mount Antigravity Brain
res_brain = brain_attach(
    folder_path=r"C:\Users\spectre\.gemini\antigravity-ide\brain",
    alias="antigravity_core",
    read_transcripts=True,
    attach_mode="lens",
)
print(res_brain)

# B. Mount Local Git Repository (extracts commit trajectories and multi-language code)
res_repo = brain_attach(
    folder_path=r"D:\GitHub\projects\Brain Harness",
    alias="brain_harness_local",
    read_commits=True,
    max_commits=50,
)
print(res_repo)

# C. Mount Remote GitHub Repository (auto-clones shallowly to cache)
res_remote = brain_attach(
    folder_path="https://github.com/fastapi/fastapi.git",
    alias="fastapi_remote",
    read_commits=True,
    max_commits=100,
)
print(res_remote)
```

## 2. Query Across Attached Brains and Repositories

Perform semantic cosine similarity queries across indexed source code, manifests, past execution transcripts, and Git commit histories:

```python
from plugins.memory_and_epistemics.brain_bridge.main import brain_query

# Query code & commit trajectories
results = brain_query(
    query="How were service keys and topological sorting implemented in plugins?",
    brain_alias="brain_harness_local",
    include_trajectories=True,
    top_k=5,
)
for r in results["results"]:
    print(f"[{r['score']}] ({r['type']}) {r['file']}: {r['snippet'][:120]}...")
```

## 3. Inspect Mounted Brains & Repositories

```python
from plugins.memory_and_epistemics.brain_bridge.main import brain_list_attached

attached = brain_list_attached()
print(f"Total sources mounted: {attached['attached_count']}")
for b in attached["brains"]:
    print(f" - {b['alias']} ({b['format']}) -> {b['summary']['total_chunks']} chunks, {b['summary'].get('detected_languages', [])}")
```

## 4. Detach a Brain or Repository

```python
from plugins.memory_and_epistemics.brain_bridge.main import brain_detach

brain_detach("brain_harness_local")
```
