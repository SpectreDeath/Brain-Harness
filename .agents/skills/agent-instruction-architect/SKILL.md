---
name: agent-instruction-architect
description: Author, audit, and iteratively maintain AGENTS.md, CLAUDE.md, and repository instruction files. Eliminate configuration smells like lint leakage and context bloat, define project execution seams, enforce dependency and permission boundaries, and implement post-incident refinement loops. Trigger when creating or editing AGENTS.md/CLAUDE.md, auditing agent instruction files, or fixing recurring agent behavior bugs.
---

# Agent Instruction Architect

`agent-instruction-architect` is the specification and repository configuration engine for agent instruction files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.windsurfrules`). It eliminates prevalent "configuration smells"—lint leakage (present in 62% of repositories), context bloat (present in 42% of repositories), contradictory directives, and generic tutorials—by engineering high-density, constraint-first instruction files that maximize agent reasoning within bounded token budgets.

Every instruction engineering session executes this five-stage progression:

```
[1. Configuration Smell Audit] → [2. Seam & Tooling Specification] → [3. Negative Boundary & Permission Injection] → [4. Exemplar & Style Binding] → [5. Post-Mortem Iteration Loop]
```

See [CARD.md](CARD.md) for the companion summary card, configuration smells taxonomy, and instruction template.
Consult `/writing-for-agents` for cognitive load principles and `/crafting-skills` for skill standards.

---

## 1. Configuration Smell Audit

Scan existing agent instruction files for the 4 primary failure patterns identified in empirical studies:

```
┌─────────────────────────────────────────────────────────────┐
│             AGENT INSTRUCTION CONFIGURATION SMELLS          │
├──────────────────────────────┬──────────────────────────────┤
│ Smell 1: Lint Leakage (62%)  │ Smell 2: Context Bloat (42%) │
│ - Pasting raw linter configs │ - Pasting generic tutorials  │
│ - Overwhelming token budget  │ - Framework 101 explanations │
├──────────────────────────────┼──────────────────────────────┤
│ Smell 3: Contradictory Rules │ Smell 4: Unbounded Scope     │
│ - Conflicting "always/never" │ - Missing "what not to touch"│
│ - Unclear precedence tiers   │ - Open-ended dependency adds │
└──────────────────────────────┴──────────────────────────────┘
```

1. **Audit Checkpoints**:
   - **Purge Generic Knowledge**: Strip basic explanations of common frameworks (e.g. "React is a component-based library...", "FastAPI uses Pydantic..."). Models already possess this knowledge.
   - **Purge Raw Lint Dumps**: Remove hundreds of lines of ESLint/Ruff rule definitions; replace with exact execution commands (`npm run lint`, `ruff check .`).
   - **Enforce Length Bounds**: Keep instruction files under 150 lines (ideal) and strictly under 300 lines. Every token in `AGENTS.md` competes directly with task reasoning.

> **Completion criterion**: Existing instruction file audited; generic tutorials, raw linter rules, and contradictory directives purged.

---

## 2. Seam & Tooling Specification

Define the explicit developer loop commands so agents interact deterministically with the repository environment:

1. **Mandatory Execution Commands**:
   - **Install**: Exact package installation command (e.g., `uv pip install -e .`, `pnpm install --frozen-lockfile`).
   - **Build**: Exact compilation/build command (e.g., `npm run build`, `cargo build`).
   - **Test**: Exact test runner and targeted test syntax (e.g., `pytest tests/unit/test_auth.py`, `pnpm test -- filter`).
   - **Lint & Format**: Exact verification and auto-fix commands (e.g., `ruff check --fix .`, `biome check --apply .`).
2. **Project Architecture Blueprint**:
   - Provide a concise map of key directory seams (e.g., `src/kernel/` — IoC container, `src/services/` — service plugins).
   - State the core architectural paradigms (e.g., "Everything is a plugin; all services resolve via typed `ServiceKey[T]`").

> **Completion criterion**: Build, test, lint, and architecture directory maps explicitly defined with verified commands.

---

## 3. Negative Boundary & Permission Injection

Provide strict negative constraints and permission boundaries—the most effective lever for preventing agent runaway:

1. **Declare "What NOT to Touch"**:
   - Identify generated directories, legacy code, vendor files, and migration histories (e.g. `src/generated/`, `db/migrations/legacy/`, `vendor/`).
   - Add explicit prohibitions: *"Do not edit files in `src/generated/`; modify schema in `schemas/` instead."*
2. **Dependency & Permission Policy**:
   - Require explicit approval before adding new third-party dependencies:
     ```markdown
     ## Dependency Policy
     - Do not add new production dependencies without prior approval.
     - Prefer existing utilities in `src/utils/` before importing external libraries.
     - If a dependency is essential, explain why and document alternatives.
     ```
3. **Execution Safety Boundaries**:
   - Block destructive operations (e.g., `git push --force`, `git reset --hard`, altering database seeds in production configs).

> **Completion criterion**: Explicit "what not to touch" section, dependency approval rule, and safety boundaries formulated.

---

## 4. Exemplar & Style Binding

Ground the agent in concrete codebase exemplars rather than abstract adjectives:

1. **Replace Abstract Taste with Concrete Pointers**:
   - *Bad (Abstract)*: "Write clean, modular, production-ready code."
   - *Good (Exemplar-Driven)*:
     ```markdown
     ## Coding Conventions
     - Follow the error handling pattern in `src/services/auth_service.py`.
     - Use `Result[T, E]` return types instead of raising raw exceptions.
     - Format all domain entities using `@dataclass(slots=True, frozen=True)`.
     ```
2. **Naming & Typing Standards**:
   - Specify explicit type strictness (e.g., Python `disallow_untyped_defs = true`, TypeScript `strict: true`).

> **Completion criterion**: Abstract advice replaced with concrete file path exemplars and strict typing rules.

---

## 5. Post-Mortem Iteration Loop

Transform agent mistakes into permanent architectural invariants in `AGENTS.md`:

```
┌─────────────────────────────────────────────────────────────┐
│              INSTRUCTION REFINEMENT CYCLE                   │
│                                                             │
│  Agent Mistake Occurs ──► Fix Code & Root Cause             │
│            │                                                │
│            ▼                                                │
│  Formulate Root Rule ───► Update AGENTS.md Boundary         │
│            │                                                │
│            ▼                                                │
│  Verify Next Run ───────► Zero Recurrence of Mistake        │
└─────────────────────────────────────────────────────────────┘
```

1. **The Post-Incident Invariant Rule**:
   - When an agent makes a mistake (e.g., edited a generated file, ran a 20-minute test suite on every minor change), do not simply fix the code. **Fix the instruction that allowed the mistake.**
2. **Formulate Positive Target Behavior**:
   - State the corrective rule positively with clear criteria (e.g., *"For UI changes, run component tests `pnpm test:ui` first; run full suite only before final submission"*).

> **Completion criterion**: Post-mortem update workflow established; instruction file updated with corrective invariant.

---

## In-File Reference: Golden Standard AGENTS.md Template

```markdown
# Repository Agent Guidelines

## 1. Quick Start & Execution Commands
- **Install**: `uv pip install -e ".[dev]"`
- **Test (Targeted)**: `pytest tests/unit/test_<module>.py`
- **Test (Full)**: `pytest`
- **Lint**: `ruff check . && mypy src/`

## 2. Architecture & Directory Seams
- `src/core/` — Core business logic and domain entities (pure Python, zero I/O).
- `src/adapters/` — Database, network, and external API integrations.
- `src/api/` — FastAPI routes and request schemas.

## 3. Mandatory Invariants & Boundaries
- **Immutable Entities**: All domain models must use `@dataclass(slots=True, frozen=True)`.
- **Do Not Touch**: Never edit files in `src/generated/` or `alembic/versions/legacy/`.
- **Dependency Guardrail**: Do not add new packages to `pyproject.toml` without explicit user approval.
- **Test Contract**: Always write failing unit tests before implementing bug fixes.

## 4. Code Exemplars
- For API endpoints, follow the structure in `src/api/v1/users.py`.
- For database transactions, follow the pattern in `src/adapters/db/session.py`.
```

---

## Anti-Patterns

- **Instruction Flooding** — Writing 600+ line instruction files that exhaust model context and cause instruction dilution.
- **Generic Tutorial Padding** — Explaining how standard libraries (e.g. React, Docker, Pytest) work rather than project-specific constraints.
- **Prohibition-Only Steering** — Using exclusively negative phrasing ("Never do X") without providing the positive replacement behavior.
- **Static Decay** — Leaving `AGENTS.md` unchanged after recurring agent bugs instead of executing the post-mortem refinement loop.
