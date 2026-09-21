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
