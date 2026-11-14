# Shim: Deterministic-First Command Router & Closed Allowlist

## Overview
- **Source Repository**: `https://github.com/Balanov/shim` (`3b5acfdf`)
- **Primary Files**:
  - `internal/router/router.go#L14-L220`

## Core Architecture & Invariants
1. **Zero-LLM Deterministic Fast Path (`Deterministic`)**: Normalizes trimmed lowercase operator text and matches multilingual `readOnly` (`/help`, `/status`, `/models`, `/skills`, `/tools`, `/mcps`, `/doctor`) and `mutating` (`/discover --add`, `/session new`) maps plus model-switch patterns (`usePattern`) before issuing any LLM completion.
2. **Bounded Compiler Fallback (`Compile`)**: Invokes the compiler model with `MaxTokens: 300`, extracts raw single-line command text (stripping optional markdown fences), and rejects unknown intents if fallback output violates grammar.
3. **Closed Slash Allowlist & Mutating Audit (`Validate`)**: Tokenizes candidates with `Split()`, requires a leading `/`, validates exact arity for `/help`, `/status`, `/doctor`, `/models`, `/skills`, `/mcps`, `/tools`, `/discover [--add]`, `/model test|use|add|remove`, `/skill show|add|remove`, `/mcp list|tools|add|remove`, `/session list|new`, `/router off|show|use`, and `/permissions <mode>`, and returns `Mutating=true` only for state-changing commands.

## Decision Heuristics & Anti-Patterns
- **Never execute unvalidated LLM-emitted slash commands directly**: Always validate arity, subcommand membership, and mutating bit via `Validate()`.
- **Never pay an LLM round-trip for static CLI shortcuts**: Keep deterministic lookup tables ahead of neural routing.
