# plugin.pr_lens_graph (v1.0.0)

PR Lens standalone animated SVG architecture diagrams, graph validation, and diff visualization

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/software_engineering/pr_lens_graph` |
| Category | `software_engineering` |
| Isolation Mode | `subprocess` |
| Services Provided | `service.pr_lens_graph` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `pr_lens_validate` | `(graph_doc)` | Validate structural typing and cross-entity semantic integrity of a graph document |
| `pr_lens_render` | `(graph_doc, config)` | Render a validated graph document into a standalone animated SVG with inline keyframes |
| `pr_lens_diff` | `(base_ref, head_ref, repo_path)` | Extract unified git diff between two commit references via safe subprocess transport |
| `pr_lens_analyze` | `(diff_text, overlay_map)` | Synthesize a structured GraphDocument and progressive walkthrough from unified diff text |
| `pr_lens_comment` | `(analysis, svg_content)` | Compose GitHub PR markdown comment enclosing standalone diagram and progressive walkthrough |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

PR Lens Graph Plugin entrypoint for Brain Harness.

#### Classes

- `class PrLensGraphPlugin` — Brain Harness Plugin providing PR Lens graph validation, rendering, diffing, and commenting.
  - `def __init__() -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def validate(graph_doc) -> PrLensValidationData`
  - `def render(graph_doc, config) -> PrLensRenderData`
  - `def diff(base_ref, head_ref, repo_path) -> PrLensDiffData`
  - `def analyze(diff_text, overlay_map) -> PrLensAnalysisData`
  - `def comment(analysis, svg_content) -> PrLensCommentData`


#### Functions

- `def pr_lens_validate(graph_doc) -> dict[str, Any]`
- `def pr_lens_render(graph_doc, config) -> dict[str, Any]`
- `def pr_lens_diff(base_ref, head_ref, repo_path) -> dict[str, Any]`
- `def pr_lens_analyze(diff_text, overlay_map) -> dict[str, Any]`
- `def pr_lens_comment(analysis, svg_content) -> dict[str, Any]`

### Module [service.py](service.py)

PR Lens Graph Service implementation.

#### Classes

- `class PrLensGraphServiceImpl` — Implementation of PrLensGraphService executing engine transformations.
  - `def validate(graph_doc) -> PrLensValidationData` — Validate structural and semantic integrity of a graph document dictionary.
  - `def render(graph_doc, config) -> PrLensRenderData` — Render a graph document into a standalone animated SVG.
  - `def diff(base_ref, head_ref, repo_path) -> PrLensDiffData` — Extract unified git diff between two commit references with Rule 14 pipe cleanup.
  - `def analyze(diff_text, overlay_map) -> PrLensAnalysisData` — Synthesize a GraphDocument from diff text and apply optional architectural overlay.
  - `def comment(analysis, svg_content) -> PrLensCommentData` — Compose GitHub PR markdown comment enclosing diagram and progressive walkthrough.


#### Functions

- `def dict_to_graph_doc(data) -> GraphDocument` — Convert raw dictionary into slotted/frozen GraphDocument entity.
- `def graph_doc_to_dict(doc) -> dict[str, Any]` — Convert GraphDocument back to serializable dictionary.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.software_engineering.pr_lens_graph.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `subprocess` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
