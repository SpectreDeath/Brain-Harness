# plugin.repo_triad_forge (v1.0.0)

Authoritative Repo-Triad Forge plugin: 5-stage repository cognitive audit, visual brief generation, Knowledge Vault commits, and verification orchestration

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/software_engineering/repo_triad_forge` |
| Category | `software_engineering` |
| Isolation Mode | `subprocess` |
| Services Provided | `service.repo_triad_forge` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `triad_inspect` | `(repo_path)` | Inspect repository structure, language manifests, and evaluate 5D compute complexity |
| `triad_briefs` | `(repo_path, output_dir)` | Scaffold 5 interactive dark-mode HTML visual briefs with Mermaid diagrams in %TEMP% |
| `triad_ki_candidates` | `(repo_path)` | Extract candidate Knowledge Items with isnad citations from repository scan |
| `triad_plan` | `(repo_path, skill_name, plugin_name)` | Synthesize 5-stage triad pipeline implementation plan with operational budgets |
| `triad_run` | `(repo_path, options)` | Execute full 5-stage triad pipeline with bounded in-flight self-repair |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Repo-Triad Forge Plugin entrypoint for Brain Harness.

#### Classes

- `class RepoTriadForgePlugin` — Brain Harness Plugin providing repository triad audit, visual briefs, and vault commits.
  - `def __init__() -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def inspect(repo_path) -> RepoInspectionData`
  - `def generate_briefs(repo_path, output_dir) -> list[TriadBriefData]`
  - `def extract_kis(repo_path) -> list[KiCandidateData]`
  - `def plan(repo_path, skill_name, plugin_name) -> TriadPlanData`
  - `def commit_kis(kis_data, vault_dir) -> list[str]`
  - `def run_pipeline(repo_path, options) -> TriadRunData`


#### Functions

- `def triad_inspect(repo_path) -> dict[str, Any]`
- `def triad_briefs(repo_path, output_dir) -> list[dict[str, Any]]`
- `def triad_ki_candidates(repo_path) -> list[dict[str, Any]]`
- `def triad_plan(repo_path, skill_name, plugin_name) -> dict[str, Any]`
- `def triad_run(repo_path, options) -> dict[str, Any]`

### Module [service.py](service.py)

Repo-Triad Forge Service implementation.

#### Classes

- `class RepoTriadForgeServiceImpl` — Implementation of RepoTriadForgeService executing engine transformations.
  - `def inspect(repo_path) -> RepoInspectionData` — Inspect repository structure and evaluate 5D compute complexity.
  - `def generate_briefs(repo_path, output_dir) -> list[TriadBriefData]` — Generate 5 interactive HTML visual briefs in output directory (or temp).
  - `def extract_kis(repo_path) -> list[KiCandidateData]` — Extract candidate Knowledge Items from repository scan.
  - `def plan(repo_path, skill_name, plugin_name) -> TriadPlanData` — Synthesize 5-stage triad pipeline implementation plan with operational budgets.
  - `def commit_kis(kis_data, vault_dir) -> list[str]` — Commit Knowledge Items to vault in canonical dual-file format (Rule 40).
  - `def run_pipeline(repo_path, options) -> TriadRunData` — Execute full 5-stage triad pipeline with bounded in-flight self-repair (Rule 25, 49).


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.software_engineering.repo_triad_forge.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `subprocess` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
