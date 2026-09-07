# Agent Skills Runtime Security, Approval Middleware & Dynamic DI

**ID:** `ki_agent_skills_runtime_security_middleware`  
**Category:** `agent_orchestration`  
**Origin:** Sergey Menshykh (*Agent Skills Specification*, Microsoft Learn / agentskills.io)  
**Provenance Lineage:** Published September 2026.

## Executive Summary
Treating AI agent skills as untrusted third-party code requires defense-in-depth runtime isolation. Because skills bundle executable instructions, data resources, and sandboxed scripts, an agent harness must govern skill execution at runtime without interrupting the autonomous agent loop for benign operations.

The Microsoft Agent Framework defines the standard runtime security model: **Tool Approval Middleware** with granular auto-approval rules, separating read-only inspection from mutating script execution, coupled with dynamic Dependency Injection (DI) and runtime keyword argument forwarding.

---

## Core Security & Runtime Mechanics

### 1. Four Skill Implementation Paradigms
1. **File-Based Skills**: Standalone directory containing `SKILL.md`, `resources/`, and `scripts/`. Simplest and most portable.
2. **Code-Defined Skills**: Inline dynamic skills registered via builder APIs (`AgentInlineSkill`) with dynamic resource delegates and script lambdas.
3. **Class-Based Skills**: Strongly-typed classes annotated with `@skill_resource` / `[AgentSkillResource]` and `@skill_script`, resolving services from the host container via constructor DI.
4. **MCP-Based Skills**: Skills bridged through Model Context Protocol (MCP) clients, enabling distributed execution across remote servers with enterprise IAM boundaries.

### 2. Tool Approval Middleware Architecture
```
┌─────────────────────────────────────────────────────────────┐
│ Agent Invocation: Skill Tool Call                          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ ToolApprovalMiddleware                                      │
├─────────────────────────────────────────────────────────────┤
│ • load_skill(name)             ──► AUTO-APPROVED (Read-Only)│
│ • read_skill_resource(name,res)──► AUTO-APPROVED (Read-Only)│
│ • run_skill_script(name,script)──► GATED / APPROVAL REQUIRED│
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       Explicit User Consent         Subprocess Sandbox Runner
       (result.user_input_requests)  (isolated venv + pipe disposal)
```

- **Read-Only Auto-Approval Rule** (`SkillsProvider.read_only_tools_auto_approval_rule`): Auto-approves context retrieval operations (`load_skill`, `read_skill_resource`), preventing agent turn interruption while inspecting guides or tables.
- **Mutating Script Gate**: Calls to `run_skill_script` trigger approval prompts or route into isolated subprocess execution sandboxes with bounded timeouts and pipe disposal invariants.

### 3. Dynamic Service & Argument Injection
Skills often need runtime application context (database connections, tenant IDs, authenticated API clients) without hardcoding credentials into markdown:
- **Dependency Injection (`IServiceProvider`)**: Script and resource functions declare service parameters resolved dynamically by the harness IoC container at runtime.
- **Keyword Forwarding (`function_invocation_kwargs` / `**kwargs`)**: Callers pass runtime arguments to `agent.run()`, which the harness securely forwards to resource and script handlers.

---

## Architectural Invariants
1. **Read-Only Separation Invariant**: Mutating scripts must never inherit read-only auto-approval rules.
2. **Subprocess Pipe Disposal Invariant**: Subprocess execution sandboxes must explicitly drain and close stdin/stdout/stderr pipes in `finally` blocks.
3. **No Secret Inlining Invariant**: Credentials, API tokens, and connection strings must be supplied via runtime DI or environment variables, never hardcoded in skill markdown files.
