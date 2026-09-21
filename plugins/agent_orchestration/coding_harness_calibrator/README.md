# Coding Harness Calibrator Plugin

Empirical component-level coding harness calibration, staging simulation, and forecasting engine grounded in the empirical laws of Fan et al. (*An Empirical Study of Harness Design for Coding Agents*, arXiv:2609.20804v1, September 2026).

## Capabilities

1. **Capability & Workload Triage**: Maps model parameters (30B, 120B, 550B+) and workload profiles (Terminal CLI vs Codebase Repo) to harness operational modes (`Scaffold`, `Balanced`, `Efficiency`).
2. **Action Space Boundary Calibration**: Optimizes tool granularity between predefined typed tools (`read_file`, `edit_file`) and bare shell (`bash`), bounding mean re-patches per task.
3. **Two-Tier Context Staging Engine ($T_4$)**: Simulates soft threshold $B_1$ (0.60 usable window) $M_1$ observation elision and hard threshold $B_2$ (0.85 usable window) $M_3$ 7-heading summarization, deprecating dead $M_2$ recall machinery.
4. **In-Flight Substrate Safeguards**: Streak-based stuck detector terminating identical failing tool actions (Streak 5 warn / Streak 8 kill).
5. **Interactive HTML Visual Brief**: Renders self-contained Tailwind + Mermaid 5-stage closed loop diagrams and empirical scorecards.

## Exported Tools

- `calibrate_harness(model_name, parameter_billions, workload, context_budget)`
- `simulate_staging(events, usable_window)`
- `predict_repatch(model_capability, action_space, workload)`
- `calibrator_visual_brief(model_name, parameter_billions, workload, output_path)`

## Service Resolution

```python
from harness.services.coding_harness_calibrator import CODING_HARNESS_CALIBRATOR_SERVICE_KEY

calibrator = context.require(CODING_HARNESS_CALIBRATOR_SERVICE_KEY)
rec = calibrator.calibrate("Claude-3.7", 550.0, "terminal_cli")
```
