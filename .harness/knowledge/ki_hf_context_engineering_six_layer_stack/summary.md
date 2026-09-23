# The Six-Layer Context Engineering Stack for Autonomous Code Agents

**ID:** `ki_hf_context_engineering_six_layer_stack`  
**Category:** `agent_orchestration`  
**Origin:** *The Context Course: Context Engineering for Code Agents* (Ben Burtenshaw et al., Hugging Face)  
**Provenance Lineage:** Commit `0b4572f`, Hugging Face, 2026.

## Executive Summary

Context engineering supersedes naive prompt engineering for production coding agents. Prompt engineering focuses on phrasing within a single conversational turn; context engineering is the systems-level discipline of giving an autonomous agent the precise instructions, dynamic tools, execution boundaries, and lifecycle hooks needed to solve complex software engineering tasks reliably without exhausting context budgets or suffering from hallucination.

The Hugging Face Context Engineering curriculum codifies an authoritative **6-layer progressive disclosure stack**:
1. **Layer 1: Skills (Portable Knowledge)** — Standardized, portable markdown instructions (`SKILL.md`) with YAML frontmatter, action triggers, and scripts for domain expertise.
2. **Layer 2: MCP (Model Context Protocol)** — Universal JSON-RPC client-server integration decoupling tools, dynamic resources, and prompt templates from model runtimes.
3. **Layer 3: Plugins (Distribution & Packaging)** — Manifest-first (`plugin.json`) bundles combining skills, MCP servers, and environment dependencies into installable units.
4. **Layer 4: Subagents (Multi-Agent Swarms)** — Specialized child agents deployed via Fan-Out/Fan-In, Pipeline, or Supervisor patterns to preserve parent context budgets.
5. **Layer 5: Hooks (Lifecycle Observation & Guardrails)** — Programmatic pre/post-tool execution interceptors capable of blocking dangerous shell operations and streaming telemetry.
6. **Layer 6: Harness Loops (ReAct Execution & Sandboxing)** — The ground-truth autonomous loop (Thought → Action → Observation) governing path confinement (`safe_path`), step limit safety, and error self-repair.

## Operational Deployment Invariants

1. **Progressive Disclosure Principle**: Never frontload entire manuals into initial agent context. Expose compact metadata in frontmatter catalogs (Tier 1), loading detailed procedures (Tier 2) only on intent activation.
2. **The M×N Universal Decoupling**: Isolate external tool APIs behind Model Context Protocol (MCP) servers rather than hardcoding vendor-specific agent bindings.
3. **The 10+ Files Context Partitioning Boundary**: When a task involves exploring or editing more than 10 files, immediately spawn isolated subagents to prevent context window blowout.
4. **Deterministic Pre-Execution Interception**: Enforce security boundaries via lifecycle hooks (`PreToolUse`) rather than relying on LLM self-restraint.
