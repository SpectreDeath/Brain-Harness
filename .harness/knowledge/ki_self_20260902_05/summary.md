# Deterministic Inward Manifest Probing for Nested Project Roots

**ID:** `ki_self_20260902_05`  
**Category:** `repository_auditing`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `hermes-agent/hermes-agent/hermes-agent`, `deep-repo-auditor/SKILL.md#stage-1`

## Executive Summary
Cloned repositories, unzipped archives, and snapshot workspaces frequently contain multi-nested root directory structures (e.g. `repo/repo/repo`). Stage 1 repository boundary detection must walk inward probing for canonical manifest files (`pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, `pom.xml`) to lock onto the true authoritative project root before launching AST and dependency inspections.

## Architectural Invariants & Rules
1. Proactively probe inward for canonical project manifests before launching AST scans.
2. The deepest directory containing a root manifest is the authoritative target root.
3. Log the detected nesting depth in session metadata to prevent redundant root resolution in subsequent stages.
