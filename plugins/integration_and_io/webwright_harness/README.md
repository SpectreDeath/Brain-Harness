# plugin.webwright_harness (v1.0.0)

SWE-style browser agent harness with trajectory skill learning, semantic retrieval, parameterized routing, persistent Chromium daemon, and multimodal verification

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/integration_and_io/webwright_harness` |
| Category | `integration_and_io` |
| Isolation Mode | `subprocess` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `webwright_skill_learn` | `(trajectory_dirs, template, library_dir)` | Synthesize reusable Python web automation skill scripts from agent trajectory runs and execution traces |
| `webwright_skill_retrieve` | `(task, k, library_dir)` | Semantically match and rank relevant candidate skills from the skill library for a target task |
| `webwright_skill_route_and_execute` | `(task, start_url, library_dir, timeout_s)` | Route a task to direct skill execution (with slot filling) or fallback to agent solving |
| `webwright_browser_session_manage` | `(action, port, headless)` | Manage persistent local Chromium browser daemons with DevTools remote debugging endpoints |
| `webwright_image_qa` | `(image_path, question, model)` | Perform high-detail multimodal visual question answering on web screenshots and DOM captures |
| `webwright_self_reflection` | `(task, screenshots_dir, action_history)` | Critique and verify task success over screenshot sequences and chronological action histories |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Webwright Harness Plugin Entrypoint & Service Implementation.

#### Classes

- `class WebwrightHarnessPlugin` — Harness Plugin providing Webwright skill learning, browser daemon, and verification services.
  - `def __init__() -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def learn_skill(trajectory_dirs, template, library_dir) -> WebwrightLearnResult`
  - `def retrieve_skills(task, k, library_dir) -> WebwrightRetrieveResult`
  - `def route_and_execute(task, start_url, library_dir, timeout_s) -> WebwrightRouteResult`
  - `def manage_browser_session(action, port, headless) -> WebwrightBrowserStatus`
  - `def image_qa(image_path, question, model) -> WebwrightImageQAResult`
  - `def self_reflect(task, screenshots_dir, action_history) -> WebwrightSelfReflectionResult`


#### Functions

- `def webwright_skill_learn(trajectory_dirs, template, library_dir) -> dict[str, Any]` — Synthesize reusable Python web automation skill scripts from agent trajectory runs and execution traces.
- `def webwright_skill_retrieve(task, k, library_dir) -> dict[str, Any]` — Semantically match and rank relevant candidate skills from the skill library for a target task.
- `def webwright_skill_route_and_execute(task, start_url, library_dir, timeout_s) -> dict[str, Any]` — Route a task to direct skill execution (with slot filling) or fallback to agent solving.
- `def webwright_browser_session_manage(action, port, headless) -> dict[str, Any]` — Manage persistent local Chromium browser daemons with DevTools remote debugging endpoints.
- `def webwright_image_qa(image_path, question, model) -> dict[str, Any]` — Perform high-detail multimodal visual question answering on web screenshots and DOM captures.
- `def webwright_self_reflection(task, screenshots_dir, action_history) -> dict[str, Any]` — Critique and verify task success over screenshot sequences and chronological action histories.

### Module [__init__.py](__init__.py)

Webwright Harness Plugin Package.
### Module [engine.py](engine.py)

Core Engine for Webwright Web Agent Trajectory Skill Synthesis & Browser Lifecycle.

#### Classes

- `class SkillMetadata` — Metadata describing a synthesized Webwright skill.
- `class BrowserDaemonState` — State of persistent local Chromium browser process.
- `class WebwrightHarnessEngine` — Production-grade Webwright engine for skill learning, routing, browser management, and evaluation.
  - `def __init__(base_dir) -> None`
  - `def learn_skill(trajectory_dirs, template, library_dir) -> dict[str, Any]` — Synthesize a reusable Python web automation skill from execution trajectories.
  - `def retrieve_skills(task, k, library_dir) -> dict[str, Any]` — Rank and retrieve skills relevant to the task.
  - `def route_and_execute(task, start_url, library_dir, timeout_s) -> dict[str, Any]` — Route a task to matching skill execution or fallback.
  - `def manage_browser_session(action, port, headless) -> dict[str, Any]` — Manage persistent local Chromium process.
  - `def image_qa(image_path, question, model) -> dict[str, Any]` — Perform multimodal VLM QA on web screenshot.
  - `def self_reflect(task, screenshots_dir, action_history) -> dict[str, Any]` — Critique and verify task success over execution history.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.integration_and_io.webwright_harness.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `subprocess` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
