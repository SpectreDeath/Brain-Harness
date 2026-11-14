```ascii
┌──────────────────────────────────────────────────────────────────────────────┐
│ SKILL: shim-harness-governor                                                 │
│ Category: agent_orchestration / runtime_harness                              │
│ Version: 1.0.0                                                               │
│ Invocation: /shim-harness-governor                                           │
│ Triggers: "shim-harness", "audit_tool_execution", "route_command",           │
│           "audit_mcp_and_discovery", "audit_session_and_skills"              │
│ Requires: "agent-harness-architect"                                          │
│ Target: Balanov/shim 4-tier sandbox, router, MCP client & skill loader       │
└──────────────────────────────────────────────────────────────────────────────┘
```

# Shim Universal AI Harness Governor — Companion Summary Card

## Pipeline Stages

| Stage | Operation | Output Model |
| --- | --- | --- |
| **1. Workspace & Tool Gate** | `audit_tool_execution()` | `WorkspaceToolSecurityReport` (`allowed`, `within_workspace`, `schema_closed`) |
| **2. Deterministic Router** | `route_command()` | `CommandRouterValidationReport` (`matched_deterministically`, `allowlisted`, `mutating`) |
| **3. MCP & Discovery Audit** | `audit_mcp_and_discovery()` | `McpAndDiscoveryReport` (`normalized_tools`, `collisions`, `uses_env_key_only`) |
| **4. Session & Skill Gate** | `audit_session_and_skills()` | `SessionAndSkillPolicyReport` (`session_id_valid`, `winning_skills`, `agents_md_truncated`) |

---

## Mandatory Invariants Checklist

- [ ] **Permission Mode & Read Bounds**: Enforce `permission_mode in {"ask", "read-only", "auto"}`, deny non-`read` tools in `read-only` mode, and require confirmation for non-`read` tools in `ask` mode.
- [ ] **Ancestor-Symlink Containment**: Resolve containment through the deepest existing ancestor symlink before opening or creating workspace targets, rejecting `"additionalProperties": true`, `> 2 MiB` / `> 2000` line reads, NUL binaries, and `> 1 MiB` shell buffers.
- [ ] **Deterministic-First Router**: Match static commands and model switches deterministically before spending `MaxTokens=300` compiler budget and enforce `ALLOWED_ROUTER_COMMANDS`.
- [ ] **MCP & Env-Ref Config**: Reject duplicate sanitized `mcp_<server>_<tool>` names within `64` chars, enforce `30s`/`60s` timeouts and `900ms` discovery budget, and forbid raw `api_key` values in config payloads.
- [ ] **Session & 4-Tier Skills**: Validate `[A-Za-z0-9_-]{1,64}` session IDs, `0o700`/`0o600` modes, `MaxSteps=16`, `64 KiB` `AGENTS.md` truncation, and `global < .shim/skills < .agents/skills < .claude/skills` precedence (`<= 1 MiB`).
