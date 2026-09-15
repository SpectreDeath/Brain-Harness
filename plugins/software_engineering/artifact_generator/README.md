# plugin.artifact_generator (v1.0.0)

Interactive HTML report generation, Mermaid diagram visualization, and executive briefings

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/software_engineering/artifact_generator` |
| Category | `software_engineering` |
| Isolation Mode | `in_process` |
| Services Provided | `service.artifact_generator` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `report_generate_html` | `(title, sections, output_path, theme)` | Generate an interactive, responsive HTML report with charts and formatted tables |
| `diagram_generate_mermaid` | `(nodes, edges, direction)` | Synthesize valid Mermaid diagram syntax from nodes and edges |
| `report_create_briefing` | `(title, summary, metrics, recommendations, output_path)` | Create an executive markdown and HTML briefing summary |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Artifact and report generator plugin for Brain Harness.

#### Classes

- `class ArtifactGeneratorPlugin` — Harness Plugin providing Mermaid diagram synthesis, HTML report generation, and executive briefings.
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def generate_mermaid(nodes, edges, direction) -> MermaidResult`
  - `def generate_html_report(title, sections, output_path, theme) -> HtmlReportResult`
  - `def create_briefing(title, summary, metrics, recommendations, output_path) -> BriefingResult`


#### Functions

- `def diagram_generate_mermaid(nodes, edges, direction) -> dict[str, Any]` — Synthesize valid Mermaid flowchart syntax.
- `def report_generate_html(title, sections, output_path, theme) -> dict[str, Any]` — Generate a responsive, standalone HTML report.
- `def report_create_briefing(title, summary, metrics, recommendations, output_path) -> dict[str, Any]` — Create a structured executive briefing document.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.software_engineering.artifact_generator.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
