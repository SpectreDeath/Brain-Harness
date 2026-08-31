# Plugin Card + Quickstart Standardization

## Problem
Plugin onboarding required ad-hoc documentation. Users and agents had no consistent entrypoint for understanding plugin capabilities, parameters, or usage patterns.

## Solution
Standardize every plugin package with two files:
- **CARD.md** — concise summary table (name, version, category, entrypoints, isolation mode, dependencies)
- **QUICKSTART.md** — minimal working examples for each entrypoint

## Operational Guideline
When scaffolding or reviewing a plugin, verify CARD.md and QUICKSTART.md exist and are up-to-date with the current plugin.json manifest. Treat missing quickstart as a validation failure.

## Provenance
- Source brain: `antigravity_core`
- Primary source: `d28bb2b5-fda7-4839-a26e-97fbc466c369.system_generated/logs/transcript.jsonl#L470`
- Distilled from: CLI validation of code-review skill card, plugin card standardization request