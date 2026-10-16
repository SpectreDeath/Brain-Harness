# HarnessCompass Plugin

**Identifier**: `plugin.harness_compass`  
**Category**: `agent_orchestration`  
**Service Provided**: `service.harness_compass` (`HARNESS_COMPASS_SERVICE_KEY`)  
**Specification**: Zhang et al. (*HarnessCompass: Guiding Automatic Harness Evolution toward Generalizable and Effective Agent Harnesses*, arXiv:2608.01918v1, 2026)  
**Knowledge Anchor**: `ki-harnesscompass-evolution`

## Overview

The `harness_compass` plugin elevates the 5-stage closed-loop HarnessCompass engine into the micro-kernel IoC container. It provides automated harness discovery, calibration, generalization gating, and R3 integration while preventing the Harness Overfitting Trilemma on coding benchmarks (e.g. SWE-Bench Verified).

## 5-Stage Evolution Pipeline

1. **Seed Initialization**: Minimal $H_0$ baseline with shell-only tool and isolated benchmark splits.
2. **Generalization Gate**: Enforces Content Invariant (zero task IDs, test files, or private symbols) and Placement Invariant (executable code vs behavioral guidance).
3. **Proactive Feedback**: Elicits Blind pre-verdict reflections and post-verdict failure attribution, discarding non-harness causes and asserting trajectory trace grounding.
4. **Dual-Track Parallel Rollout**: Disjoint evaluation of Track A (Structural) vs Track B (Guidance).
5. **R3 Integration & Occam's Redundancy Purge**: Revision (conservative loser triage) $\rightarrow$ Recombination (winner precedence) $\rightarrow$ Refinement (Occam's razor deletion of advisory rules duplicated by code mechanisms).

## Tool Entrypoints

- `validate_gate`: Validate candidate harness edit against Content and Placement invariants.
- `ground_feedback`: Ground agent usability feedback and check trace citations.
- `merge_r3`: Execute R3 integration (Revision, Recombination, Occam's Razor).
- `run_evolution_round`: Simulate a full 5-stage closed loop evolution and acceptance round.
- `harness_compass_visual_brief`: Generate interactive standalone HTML visual brief.


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `validate_gate` | `(id, surface, description, target_file, content, is_advisory, is_code_executable)` | Validate candidate harness edit against Content and Placement invariants |
| `ground_feedback` | `(kind, component, friction, desired_change, trace_refs, attribution, trajectory_turns)` | Ground agent usability feedback and check trace citations |
| `merge_r3` | `(winner_name, winner_score, winner_edits, loser_name, loser_score, loser_edits)` | Execute R3 integration: Revision, Recombination, and Occam's Razor Refinement |
| `run_evolution_round` | `(round_num, baseline_score, structural_edits, guidance_edits, structural_score, guidance_score)` | Simulate a complete 5-stage closed loop evolution and acceptance round |
| `harness_compass_visual_brief` | `(output_path)` | Generate interactive HTML visual brief with telemetry and Mermaid DAG |
