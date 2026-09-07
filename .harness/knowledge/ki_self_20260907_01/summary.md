# Deep-Module 3-Layer Architecture Graduation Pattern

**ID:** `ki_self_20260907_01`  
**Category:** `architecture`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `ba193963/walkthrough.md`, `0ba8e765/walkthrough.md`, `14712712/walkthrough.md`, `0d817804/walkthrough.md`, `35ea24c3/walkthrough.md`, `AGENTS.md#Rule1`, `AGENTS.md#Rule2`

## Executive Summary
Skill scripts and standalone utilities in Brain Harness must graduate through a strict 3-layer architecture hierarchy rather than remaining isolated CLI scripts or loose helper functions. Across 5 consecutive deepening sessions spanning Sep 3–7, 2026, this pattern achieved a 100% test pass rate, zero regression rate, and seamless kernel IoC container integration.

## The 3-Layer Architecture Hierarchy

1. **Layer 1: Execution & Script Boundary (CLI / Shim)**
   - Standalone CLI scripts (`scripts/*.py`) are preserved for backwards compatibility.
   - When an engine is extracted, the script is refactored into a thin, single-line delegation shim that imports the engine facade, instantiates it, and invokes its typed execution method.
   - Scripts are **never deleted**, preventing breakage of external automation, subprocess calls, or legacy shell pipelines.

2. **Layer 2: Engine Facade (Pure Domain Core)**
   - Pure domain business logic resides in a cohesive engine class (e.g., `DataManagementEngine`, `FileAnalysisEngine`, `LadderEvaluator`).
   - All input arguments and return payloads are typed with slotted, frozen dataclasses (`@dataclass(slots=True, frozen=True)`).
   - The engine facade has zero dependencies on CLI parsers (`click`, `argparse`) or environment variable side effects.

3. **Layer 3: Kernel IoC Service Registration (`ServiceKey[T]`)**
   - Registered into the IoC micro-kernel container using typed service keys (`DATA_MANAGEMENT_SERVICE_KEY: ServiceKey[DataManagementService]`).
   - Implements abstract service protocols (`context.provide(key, service)` and `context.require(key)`).
   - Allows autonomous agent loops, background tools, and MCP servers to resolve capabilities without hardcoded imports.

## Empirical Validation
- **DataManagementEngine** (`ba193963`): Consolidated 4 standalone procedural scripts into a single unified facade, achieving 17/17 tests passing in 1.25s.
- **FileAnalysisEngine** (`0ba8e765`): Transformed loose analysis functions into `FileAnalysisEngine` + `GroundingCatalog` + `GroundingAuditor` (20/20 tests passing).
- **LadderEvaluator** (`14712712`): Modularized ad-hoc evaluations into `LadderEvaluator`, `CapabilityProfiler`, and `DynamicModelRouter` (46/46 tests passing).
- **LegacyArchaeologist** (`0d817804`): Formalized legacy seam inspection and characterization harness (8/8 tests passing).
- **DocLinter** (`35ea24c3`): Diátaxis taxonomy documentation engine (8/8 tests passing).
