# Dual-Mode Simulation-Backed Engine for Native System Sandboxes

## Context
Extracted during autobiographical self-reflection (/harness-reflector) across execution trajectories and visual briefs.

## Distilled Learning
External tools and plugins often depend on platform-specific C++/Rust binaries, OS accessibility daemons, or display servers (UI Automation, AXUIElement, AT-SPI) that are absent or uncompiled in CI/CD runners and test containers. Implementing a dual-mode domain engine with an automatic simulation fallback allows the complete test suite (IoC resolution, protocol contracts, schema validation, and tool wrappers) to pass with 100% determinism while strictly isolating the real subprocess runner behind Rule 14 and Rule 53 transport safety nets.

## Triggers & Seam Choices
- **Trigger**: AI coding agent tool dispatch, subprocess runner construction, or architecture boundary enforcement.
- **Seam Choice**: Integration via Brain Harness IoC container, tool execution runners, and CI linting pipelines.
