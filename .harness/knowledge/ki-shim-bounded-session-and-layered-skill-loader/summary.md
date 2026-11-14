# Shim: Bounded Session Store, Agent Loop & 4-Layer Skill Loader

## Overview
- **Source Repository**: `https://github.com/Balanov/shim` (`3b5acfdf`)
- **Primary Files**:
  - `internal/agent/agent.go#L28-L102`
  - `internal/session/session.go#L27-L133`
  - `internal/skills/skills.go#L31-L150`

## Core Architecture & Invariants
1. **Bounded ReAct Loop & Instruction Budget (`agent.go`)**: Defaults `MaxSteps = 16`, requests `MaxTokens = 8192` per turn, caps injected `AGENTS.md` project context at `64 KiB` (`64<<10`), and explicitly frames retrieved content as untrusted data.
2. **Hardened Append-Only JSONL Sessions (`session.go`)**: Generates `YYYYMMDD-HHMMSS-<4-byte crypto/rand hex>` identifiers, validates caller-supplied IDs via `validID()` (`1..64` characters matching `[A-Za-z0-9-_]`), isolates files under `0o700` dirs / `0o600` JSONL logs, and configures scanner buffers up to `16 MiB` (`16<<20`).
3. **4-Tier Skill Precedence & Lazy Hydration (`skills.go`)**: Loads candidate skills in increasing precedence (`GlobalDir` < `.shim/skills` < `.agents/skills` < `.claude/skills`) so project-local definitions cleanly override global ones, verifies closed YAML frontmatter within `1 MiB` (`1<<20`), and exposes on-demand `load_skill` (`Level: Read`).

## Decision Heuristics & Anti-Patterns
- **Never load full skill bodies eagerly into every turn prompt**: Register a `Read`-level `load_skill` tool and cap individual files at `1 MiB`.
- **Never accept unvalidated session IDs in file paths**: Reject traversal characters outside `[A-Za-z0-9-_]` and length `1..64` before opening `.jsonl` logs.
