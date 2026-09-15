# plugin.brain_bridge (v1.1.0)

Mounts, inspects, and federates external agent brains, Git/GitHub repositories, IDE transcripts, and knowledge libraries

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/memory_and_epistemics/brain_bridge` |
| Category | `memory_and_epistemics` |
| Isolation Mode | `in_process` |
| Services Provided | `service.brain_bridge` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `brain_attach` | `(folder_path, alias, read_transcripts, read_commits, max_commits, attach_mode)` | Inspect and mount an external brain, Git repository (local path or remote URL), IDE state, or knowledge directory |
| `brain_query` | `(query, brain_alias, include_trajectories, top_k)` | Query across one or all mounted external brains/repos for knowledge, code, solutions, or trajectories |
| `brain_list_attached` | `()` | List all currently mounted external brains and repositories, their detected formats, and index statistics |
| `brain_detach` | `(brain_alias)` | Unmount a foreign brain or repository and release its memory indexes |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Federated Brain Bridge & Repository Attachment Plugin for Brain Harness.

#### Classes

- `class BrainBridgeEngine` — Encapsulated engine managing external brain and repository attachments.
  - `def __init__() -> None`
  - `def attach(folder_path, alias, read_transcripts, read_commits, max_commits, attach_mode) -> dict[str, Any]`
  - `def query(query, brain_alias, include_trajectories, top_k) -> dict[str, Any]`
  - `def list_attached() -> dict[str, Any]`
  - `def detach(brain_alias) -> dict[str, Any]`
- `class BrainBridgePlugin` — Harness Plugin providing federated external brain and Git repository attachment services.
  - `def __init__(engine) -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def attach(folder_path, alias, read_transcripts, read_commits, max_commits, attach_mode) -> BrainAttachResult`
  - `def attach_async(folder_path, alias, read_transcripts, read_commits, max_commits, attach_mode) -> BrainAttachResult`
  - `def query(query, brain_alias, include_trajectories, top_k) -> BrainQueryResult`
  - `def query_async(query, brain_alias, include_trajectories, top_k) -> BrainQueryResult`
  - `def list_attached() -> BrainListResult`
  - `def detach(brain_alias) -> BrainDetachResult`


#### Functions

- `def brain_attach(folder_path, alias, read_transcripts, read_commits, max_commits, attach_mode) -> dict[str, Any]` — Inspect and mount an external brain, repository, IDE state, or knowledge directory.
- `def brain_query(query, brain_alias, include_trajectories, top_k) -> dict[str, Any]` — Query across one or all mounted external brains/repos for knowledge, code, solutions, or trajectories.
- `def brain_list_attached() -> dict[str, Any]` — List all currently mounted external brains/repositories, their detected formats, and index statistics.
- `def brain_detach(brain_alias) -> dict[str, Any]` — Unmount a foreign brain or repository and release its memory indexes.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.brain_bridge.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
