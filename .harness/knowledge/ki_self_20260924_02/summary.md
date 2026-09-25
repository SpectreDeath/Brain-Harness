# Dual-Silo CLI Consolidation, Slotted Domain Engine Architecture, and IoC Service Elevation (discovery-index-scout)

## Problem
In developer skills and agent tooling, scripts frequently proliferate as ad-hoc CLI commands. In `discovery-index-scout`:
1. `search_index.py` contained a hardcoded in-memory Python list of 46 curated sources, unable to see dynamic sources added by users.
2. `catalog_registry.py` maintained a separate local file (`registry.json`) with its own CRUD methods, devoid of search scoring or ranking algorithms.
3. `config.default.yaml` defined operational parameters and extra sources that were completely ignored by `search_index.py`.
4. ReAct agent step execution engines (`StepExecutionEngine`) executing skill tasks were forced to fork external Python subprocesses (`python scripts/search_index.py --query ...`), incurring high process-spawn latency and losing structured typing.

## Solution
1. **Slotted Domain Engine**: Implemented `DiscoveryCatalogEngine` in `.agents/skills/discovery-index-scout/scripts/discovery_engine.py` using `slots=True` and `frozen=True` dataclass models (`DiscoverySource`). The engine unifies 46 curated baseline sources, `registry.json` entries, and 3-tier config `extra_sources`.
2. **Weighted Multi-Field Search**: Implemented query ranking with term-frequency saturation, field weighting (name: 3.0, description: 1.5, categories: 2.0, tags: 1.5), and faceted filtering (category, access tier, format).
3. **Thin Delegator CLI Frontends**: Refactored `search_index.py` and `catalog_registry.py` into thin shims delegating to `DiscoveryCatalogEngine`, preserving 100% backward compatibility for human terminal use.
4. **IoC Micro-Kernel Elevation**: Formulated `DiscoveryIndexService` protocol in `src/harness/services/discovery_index.py` and authored `DiscoveryIndexScoutPlugin` in `plugins/data_engineering/discovery_index_scout/main.py` exporting `plugin = DiscoveryIndexScoutPlugin()` (Rules 18, 45, and 49).

## Operational Guideline
- Always unify static source lists and dynamic persistence files into a single authoritative domain model.
- Elevate tool capabilities to typed IoC services for in-memory ReAct agent execution while keeping CLI scripts as thin wrappers.
- Verify adherence via contract test suites asserting ranking, filtering, and IoC registration (e.g. `tests/unit/test_discovery_index_scout.py`).

## Provenance
- Source files: `src/harness/services/discovery_index.py`, `plugins/data_engineering/discovery_index_scout/main.py`, `.agents/skills/discovery-index-scout/scripts/discovery_engine.py`
- Visual Brief: `%TEMP%/architecture-review-discovery-index-scout-20260924-223255.html`
- Unit Test Suite: `tests/unit/test_discovery_index_scout.py` (11/11 passing)
- Architectural Standards: `AGENTS.md` Rules 18, 44, 45, 49
