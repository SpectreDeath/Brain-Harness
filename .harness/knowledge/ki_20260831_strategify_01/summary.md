# SubsystemRegistry & Modular Simulation Orchestration

## Metadata
- **KI ID**: `ki_20260831_strategify_01`
- **Source Target**: `D:\GitHub\projects\Strategify`
- **Format**: `python_simulation_harness`
- **Timestamp**: `2026-08-31T23:15:00Z`
- **Status**: `VERIFIED`

## Distilled Learning
# KI: SubsystemRegistry & Modular Simulation Orchestration

## Operational Summary
Complex Agent-Based Models (ABM) tend to accumulate disparate domain subsystems (trade, supply chain, coalitions, epidemiology, escalation, temporal dynamics, propaganda, logic bridges) directly inside the central model class, leading to severe coupling and flaky step sequences. Centralizing subsystem initialization and sequential execution into a dedicated `SubsystemRegistry` provides clean dependency injection, configurable feature flags, and deterministic step ordering without polluting the core simulation state.

## Primary Lineage
- **Assertion**: SubsystemRegistry encapsulates the lifecycle, configuration, and strict deterministic stepping of 17 heterogeneous simulation subsystems, eliminating god-object coupling in agent-based models.
  - `primary_code`: `strategify/sim/subsystem_registry.py#L1-L214` (Verified: True)
  - `primary_code`: `strategify/sim/model.py#L1-L350` (Verified: True)
  - `visual_brief`: `C:/Users/spectre/AppData/Local/Temp/data-topology-review-20260831-231500.html` (Verified: True)
