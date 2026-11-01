---
name: context-type-system
description: Govern LLM prompt context through four partitioned semantic channels with immutable provenance ledgers, tool output elevation, and quota-budgeted assembly. Do not use for generic text summarization, unpartitioned prompt concatenation, or ad-hoc string formatting.
cluster: memory_and_epistemics
---

# Context Type System & Semantic Provenance Ledger

## Overview

The `context-type-system` skill governs the assembly, provenance tracking, and type enforcement of LLM context windows. It segregates prompt inputs into four immutable semantic channels:
1. `instruction`: High-priority operational directives and developer task goals.
2. `evidence`: Formally validated observations, grep extracts, and test results.
3. `memory`: Long-term or working-memory state recalled from external stores.
4. `tool_output`: Unsanitized raw outputs from shell commands, APIs, or subprocess tools.

Cross-channel transitions are strictly governed by policy: raw `tool_output` can **never** be injected as `instruction` (preventing indirect prompt injection), and can only elevate to `evidence` after passing structural or schema validation.

```
┌─────────────────────────────────────────────────────────────┐
│                       Context Pipeline                      │
└──────────────────────────────┬──────────────────────────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│ Instruction  │        │    Memory    │        │ Tool Output  │
│  (Protected) │        │  (Recalled)  │        │ (Unverified) │
└──────┬───────┘        └──────┬───────┘        └──────┬───────┘
       │                       │                       │
       │                       │                       ▼ validate_tool_output
       │                       │                ┌──────────────┐
       │                       │                │   Evidence   │
       │                       │                │  (Elevated)  │
       │                       │                └──────┬───────┘
       │                       │                       │
       └───────────────────────┼───────────────────────┘
                               ▼
               ┌───────────────────────────────┐
               │    Context Assembler (Quota)  │
               └───────────────┬───────────────┘
                               ▼
               ┌───────────────────────────────┐
               │   Rendered Budgeted Prompt    │
               └───────────────────────────────┘
```

---

## Visual Brief

### Architecture
- **Provenance Ledger**: Tracks initial item registration and subsequent transformation hops back to the root observation.
- **Budget Allocator**: Ensures context windows do not exceed token caps while allocating reserved quotas to each semantic channel.
- **Policy Enforcement**: Prevents unauthorized channel hops and logs audit trails.

### Verification Flow
1. Register inputs via `harness context add`.
2. Inspect or elevate tool results via `harness context validate-tool`.
3. Assemble budgeted prompt with `harness context assemble`.
4. Audit lineage via `harness context ledger`.

---

## Workflow Steps

### Phase 1: Context Ingestion and Channel Tagging
Register inputs into their designated channels:
```bash
harness context add --session my-run --type instruction --content "Refactor auth module"
harness context add --session my-run --type memory --content "Previous fix in commit abc1234"
```

### Phase 2: Tool Execution and Validation
Stage raw tool output and promote to evidence:
```bash
harness context validate-tool --session my-run --tool-name "git-status" --output-json '{"status": "clean"}'
```

### Phase 3: Budgeted Assembly
Render the assembled prompt partitioned by semantic headers:
```bash
harness context assemble --session my-run --budget-tokens 4000 --json
```

### Phase 4: Provenance Audit
Trace multi-hop Isnad provenance:
```bash
harness context ledger --session my-run --json
```

---

## Mandatory Checkpoints

- [ ] **Channel Isolation**: Verify that raw `tool_output` cannot be registered as `instruction`.
- [ ] **Validation Gate**: Verify that `validate-tool` promotes items with a newly generated `evidence` ID.
- [ ] **Budget Cap**: Verify that assembled tokens do not exceed the specified budget ceiling.

---

## Anti-Patterns

- **Raw String Splice** — Concatenating untyped raw tool outputs directly into agent instructions.
- **Unverified Promotion** — Elevating tool output to evidence without structural or schema validation.
- **Unbudgeted Assembly** — Rendering prompts without token ceilings or channel quotas.
- **Unlinked Transformations** — Mutating item types without recording parent lineage in the provenance ledger.

---

## Related Skills & Docs

- [Ebbinghaus Memory Governor](../ebbinghaus-memory-governor/SKILL.md)
- [Learning Core Lifecycle Narrative](../../docs/explanation/learning-core-lifecycle.md)
- [Context Command Reference](../../docs/reference/cli.md)

