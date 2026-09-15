# plugin.stagehand_browser (v1.0.0)

Browserbase's next-generation AI browser automation engine with Act, Extract, Observe, and WebMCP protocol integration

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/integration_and_io/stagehand_browser` |
| Category | `integration_and_io` |
| Isolation Mode | `subprocess` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `stagehand_act` | `(action, model, timeout_s, variables)` | Execute high-level natural language actions (clicks, keyboard input, navigation) on active page |
| `stagehand_extract` | `(instruction, schema, model, use_text_extract)` | Extract structured data matching a target JSON schema directly from live DOM & rendered layout |
| `stagehand_observe` | `(instruction, model, return_action)` | Inspect live DOM to return interactive elements, locators, and suggested next actions |
| `stagehand_webmcp_tool_invoke` | `(tool_name, arguments, page_id)` | Discover and invoke WebMCP (Web Model Context Protocol) tools exposed by web pages |
| `stagehand_session_control` | `(action, url, script, provider)` | Manage browser session lifecycle, navigation, JavaScript evaluation, and page capture |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Stagehand Browser Plugin Entrypoint & Service Implementation.

#### Classes

- `class StagehandBrowserPlugin` — Harness Plugin providing Stagehand Next-Gen Browser Automation, Act, Extract, Observe, and WebMCP.
  - `def __init__() -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def act(action, model, timeout_s, variables) -> StagehandActResult`
  - `def extract(instruction, schema, model, use_text_extract) -> StagehandExtractResult`
  - `def observe(instruction, model, return_action) -> StagehandObserveResult`
  - `def invoke_webmcp_tool(tool_name, arguments, page_id) -> StagehandWebMCPResult`
  - `def control_session(action, url, script, provider) -> StagehandSessionStatus`


#### Functions

- `def stagehand_act(action, model, timeout_s, variables) -> dict[str, Any]` — Execute high-level natural language actions (clicks, keyboard input, navigation) on active page.
- `def stagehand_extract(instruction, schema, model, use_text_extract) -> dict[str, Any]` — Extract structured data matching a target JSON schema directly from live DOM & rendered layout.
- `def stagehand_observe(instruction, model, return_action) -> dict[str, Any]` — Inspect live DOM to return interactive elements, locators, and suggested next actions.
- `def stagehand_webmcp_tool_invoke(tool_name, arguments, page_id) -> dict[str, Any]` — Discover and invoke WebMCP (Web Model Context Protocol) tools exposed by web pages.
- `def stagehand_session_control(action, url, script, provider) -> dict[str, Any]` — Manage browser session lifecycle, navigation, JavaScript evaluation, and page capture.

### Module [__init__.py](__init__.py)

Stagehand Browser Plugin Package.
### Module [engine.py](engine.py)

Core Engine for Stagehand Next-Generation Web Automation, Act, Extract, Observe, and WebMCP.

#### Classes

- `class StagehandSession` — Active Stagehand browser session.
- `class StagehandBrowserEngine` — Production Stagehand engine orchestrating NL Act, Schema Extract, DOM Observe, and WebMCP.
  - `def __init__() -> None`
  - `def act(action, model, timeout_s, variables, session_id) -> dict[str, Any]` — Execute high-level natural language actions on page.
  - `def extract(instruction, schema, model, use_text_extract, session_id) -> dict[str, Any]` — Extract structured data matching target JSON schema from page DOM.
  - `def observe(instruction, model, return_action, session_id) -> dict[str, Any]` — Inspect live DOM to return interactive elements, locators, and actions.
  - `def invoke_webmcp_tool(tool_name, arguments, page_id, session_id) -> dict[str, Any]` — Discover or invoke a WebMCP tool exposed on the active page.
  - `def control_session(action, url, script, provider, session_id) -> dict[str, Any]` — Manage browser session lifecycle, navigation, and evaluation.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.integration_and_io.stagehand_browser.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `subprocess` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
