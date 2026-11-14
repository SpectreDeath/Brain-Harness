---
name: shim-harness-governor
description: Govern universal CLI agent loops, 4-tier tool permissions, ancestor-symlink workspace sandboxes, deterministic-first command routing, collision-safe MCP namespacing, and layered skill loading. Do not use for static UI styling or external SQL analytics.
---

# Shim Universal AI Harness Governor

`shim-harness-governor` distills the bounded CLI agent runtime from `Balanov/shim` (`3b5acfdf`) into the Brain Harness IoC micro-kernel via [`ShimHarnessGovernorProtocol`](../../../src/harness/services/shim_harness_governor.py).

See [CARD.md](CARD.md) for the companion summary card, pipeline stages, and mandatory invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline operational limits and [scripts/shim_governor_engine.py](scripts/shim_governor_engine.py) for CLI execution.

---

## 1. Tiered Capability Gating & Ancestor-Symlink Workspace Sandbox

1. **Enforce Permission Modes & Strict Schemas (`audit_tool_execution`)**: Partition tools under `read`, `write`, `shell`, and `external`; reject non-`read` tools in `read-only` mode, require explicit confirmation in `ask` mode, and require `"additionalProperties": false` on tool parameter schemas.
2. **Canonicalize Deepest Existing Ancestors (`within`)**: Resolve symlinks across the workspace root and deepest existing parent directory of each target path before checking containment, rejecting files over `2 MiB`, ranges above `2000` lines, NUL-byte binaries, and shell output past `1 MiB` (`120s` timeout).

> **Completion criterion**: `WorkspaceToolSecurityReport` confirms `allowed=True`, `within_workspace=True`, and `schema_closed=True`.

---

## 2. Deterministic-First & Closed-Allowlist Command Routing

1. **Zero-LLM Fast Path (`route_command`)**: Resolve normalized static commands (`/help`, `/status`, `/doctor`, `/models`, `/skills`, `/tools`, `/mcps`, `/discover --add`, `/session new`) and model switches (`/model use <name>`) deterministically without model latency.
2. **Closed Allowlist Verification**: Strip markdown fences from bounded `MaxTokens=300` compiler fallbacks, tokenize arguments safely, reject any command outside `ALLOWED_ROUTER_COMMANDS`, and expose an explicit `mutating` flag.

> **Completion criterion**: `CommandRouterValidationReport` returns `allowlisted=True` with accurate `mutating` classification.

---

## 3. Collision-Free MCP Namespacing, Env-Ref Config & Layered Session/Skill Governance

1. **Sanitize MCP Tools & Discovery (`audit_mcp_and_discovery`)**: Map external tools to `mcp_<server>_<tool>` (`[A-Za-z0-9_-]`, `<= 64` chars) with strict collision failure, enforce `30s`/`60s` timeouts and `900ms` local discovery sorting, and prohibit raw `api_key` values in config (`api_key_env` only).
2. **Bound Agent Loops, JSONL Sessions & 4-Tier Skills (`audit_session_and_skills`)**: Enforce `MaxSteps=16`, `64 KiB` `AGENTS.md` bounds, `[A-Za-z0-9_-]{1,64}` session IDs (`0o700`/`0o600`, `16 MiB` scanner), and `global < .shim/skills < .agents/skills < .claude/skills` last-wins skill loading (`<= 1 MiB` with closed YAML frontmatter).

> **Completion criterion**: `McpAndDiscoveryReport` and `SessionAndSkillPolicyReport` confirm collision-free tooling, env-ref hygiene, and valid precedence.

---

## The Three Foundational Pillars

### 1. Ancestor-Canonical Containment Over Shallow Path Checks
Always resolve symlinks through the deepest existing ancestor directory alongside the canonicalized workspace root so creating new leaf files cannot escape through symlinked parent directories.

### 2. Deterministic Bypass Ahead of Allowlisted Compilation
Serve common operator queries deterministically before invoking bounded `MaxTokens=300` compilation, and gate every emitted command against a closed slash allowlist with mutating labels.

### 3. Bounded Context, Env-Ref Secrets & Collision-Safe MCP Surfaces
Keep secrets out of config files via `api_key_env`, detect `64`-character sanitized MCP identifier collisions immediately, bound logs/files (`1 MiB` / `2 MiB` / `16 MiB`), and hydrate skills lazily using `load_skill`.

---

## Anti-Patterns

- **Shallow `abspath` Containment** — Resolving only syntactic paths fails when creating new leaf files beneath symlinked directories; always canonicalize the deepest existing ancestor first.
- **Blind MCP Tool Truncation** — Truncating `mcp_<server>_<tool>` to 64 characters without collision tracking silently overwrites sibling tools.
- **Unvalidated Compiler Output** — Executing model-generated slash commands without closed-allowlist arity and `mutating` verification invites arbitrary state mutation.
- **Raw Secret Persistence** — Writing literal `api_key` tokens into config files instead of `api_key_env` variable names leaks credentials on disk.
- **Eager Skill Hydration** — Dumping all skill markdown bodies into every turn bloats prompts; inject metadata summaries and expose a `Read`-tier loader bounded to `1 MiB`.
