# Planted-Violation Self-Testing Architecture Boundary Gate

## Context
Extracted during autobiographical self-reflection (/harness-reflector) across execution trajectories and visual briefs.

## Distilled Learning
Static analysis linters and architecture boundary checkers can silently rot over time as codebases evolve and dependencies shift. The planted-violation self-testing pattern requires the verification script to plant deliberate synthetic violations of every architectural boundary rule in a temporary workspace copy before running against production files. If any rule fails to detect its planted violation, CI immediately aborts, ensuring the verification harness remains perpetually infallible.

## Triggers & Seam Choices
- **Trigger**: AI coding agent tool dispatch, subprocess runner construction, or architecture boundary enforcement.
- **Seam Choice**: Integration via Brain Harness IoC container, tool execution runners, and CI linting pipelines.
