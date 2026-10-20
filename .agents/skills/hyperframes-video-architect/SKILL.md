---
name: hyperframes-video-architect
description: Architect, generate, and compose programmatic motion graphics and video timelines from code, diffs, and agent trajectories using HyperFrames and GSAP. Do not use for raw video encoding, non-web 3D rendering, or audio processing.
---

# HyperFrames Video Architect

Architect and compose programmatic video sequences and timeline motion graphics using HyperFrames, Tailwind CSS, and GSAP.

## 1. Scene Topology Decomposition
Deconstruct video narratives into discrete, self-contained `VideoScene` instances. Assign deterministic durations ($1000\text{ms} \le t \le 10000\text{ms}$) and explicit transition types (`fade`, `slide`, `zoom`).
> **Completion criterion**: All narrative steps partitioned into validated `VideoScene` instances with non-empty templates and valid durations.

## 2. Web Animation Architecture
Author HTML templates utilizing Tailwind CSS utility classes and inline GSAP timeline declarations. Enforce fixed 16:9 aspect ratios ($1280 \times 720$ or $1920 \times 1080$) and pure web standards.
> **Completion criterion**: Standalone HTML templates render without external asset stalls or missing dependencies.

## 3. Subprocess Bridge Invocation
Dispatch render requests via `HyperFramesService.render_async()` or headless preview simulation. Verify subprocess stdout/stderr drainage in `finally` blocks (Rule 14).
> **Completion criterion**: Output video artifact or deterministic JSON bundle generated with positive frame count and recorded execution time.

## Anti-Patterns

- **Unbounded Scene Durations** — Creating scenes longer than 15 seconds without intermediate transition cuts leads to viewer fatigue.
- **External Asset Latency** — Referencing un-cached external media URLs inside HTML templates causes render stalls and headless timeouts.
- **Subprocess Pipe Leaks** — Neglecting explicit stdin/stdout drainage in exception paths deadlocks worker proactors.
- **Missing Zero-Fork Config** — Hardcoding video resolutions or frame rates directly in scripts rather than consuming operational defaults.

## Related Skills

- [pr-lens-visualizer](../pr-lens-visualizer/SKILL.md) — Render Git diffs as static SVGs.
- [cellcog-multimodal](../cellcog-multimodal/SKILL.md) — Multi-agent multimodal asset coordination.