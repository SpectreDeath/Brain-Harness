# Semantic DOM Extraction & Self-Healing Web Action Primitives

## Context
Raw DOM scraping produces massive HTML trees with thousands of decorative elements, causing token exhaustion and brittle selector failures when dynamic websites change classes or layouts.

## Distilled Learning
Structure browser agent automation around 3 semantic action primitives:
- `observe()`: Distill the page into a sanitized accessibility tree containing only interactive elements (buttons, inputs, links) with unique xpath/coordinate bindings.
- `act(instruction)`: Translate natural language goals (e.g. "click the login button") into verified DOM actions with automatic retry on selector drift.
- `extract(schema)`: Extract structured data directly into typed schemas using LLM-guided element localization.

## Triggers & Seam Choices
- **Trigger**: Autonomous browser workflows, web data extraction, and web dashboard verification.
- **Seam Choice**: Encapsulate in `plugins/integration_and_io/stagehand_browser/` (Rule 18 & 24) via headless CDP / Playwright bridge.
