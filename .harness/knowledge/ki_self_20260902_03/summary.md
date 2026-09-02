# Artifact Boundary Isolation & Workspace Tool Scaffolding

**ID:** `ki_self_20260902_03`  
**Category:** `tooling_and_scaffolding`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `transcript.jsonl#step-write-to-file`, `AGENTS.md#Rule31`

## Executive Summary
The IDE `write_to_file` tool strictly enforces that `ArtifactMetadata` is only valid for files located within the conversation artifact directory (`<appDataDir>/brain/<conversation-id>/`). When creating or scaffolding repository workspace files, plugin packages, or test suites, either omit `ArtifactMetadata` entirely or utilize `run_command` with a Python writer script.

## Architectural Invariants & Rules
1. `ArtifactMetadata` must ONLY be passed when writing directly to the conversation artifact directory.
2. Workspace plugin code and manifests must omit `ArtifactMetadata` to prevent system policy rejection.
3. Bulk file scaffolding across multiple repository directories should use dedicated Python generator scripts.
