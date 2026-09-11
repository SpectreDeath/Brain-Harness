```
┌────────────────────────────────────────────────────────┐
│               SKILL: agent-skill-sdlc                  │
├────────────────────────────────────────────────────────┤
│ SKILL:        agent-skill-sdlc                          │
│ Category:    engineering_and_sdlc                      │
│ Domain:      Engineering / Meta-Skills                 │
│ Invocation:  /agent-skill-sdlc                         │
│ Triggers:    "build agent skill", "skill sdlc",        │
│              "test agent skill", "validate skill",     │
│              "configurable agent skill", "repair tool" │
│ Version:     1.0.0                                     │
│ Isolation:   in-process                                │
│ Provides:    "service.agent_skill_sdlc"                │
├────────────────────────────────────────────────────────┤
│ Target:      Autonomous agent skill lifecycle engine   │
│              covering design, config, testing, audit.  │
└────────────────────────────────────────────────────────┘
```

# Agent Skill SDLC — Companion Summary Card

`agent-skill-sdlc` provides a standardized, deep-module software development lifecycle for authoring, configuring, validating, testing, and auditing AI agent skills across their complete evolutionary arc (v1 prompt snippet to v5 multi-engine distributed skill).

See [SKILL.md](SKILL.md) for the complete 5-phase operational procedure.
Related skills: `/crafting-skills` for craft guidelines, `/book-to-skill-forge` for literature extraction, and `/epistemic-isnad-audit` for claim traceability.

---

## 5-Phase Progression Table

| Phase | Objective | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Phase 1: Trigger Engineering & System Architecture** | Define strict activation boundaries, negative bounds, and decoupled interfaces | `SKILL.md` (frontmatter & bounds) | `Trigger matrix validated` |
| **Phase 2: Configuration & Deep-Module Decoupling** | Implement 3-tier config precedence and additive lists without forking | `config.default.yaml` + `resolve_config.py` | `Config resolution clean` |
| **Phase 3: Bundled Scripts & Local Salvage Loops** | Implement deterministic python tooling and local string salvage routines | `scripts/` + salvage utilities | `Scripts verified non-interactive` |
| **Phase 4: Two-Phase Validation & Behavioral Verification** | Execute syntactic and semantic rule checks with path-targeted repair | `validate_skill.py` | `Two-phase validation passes` |
| **Phase 5: Security Auditing & Pre-Flight Graduation** | Run SkillSpector 70-pattern security audit and verify pre-flight checklist | Security scorecard & Skill Graph commit | `Pre-flight score <= 20` |

---

## The Three Foundational Craft Pillars

1. **The Visual Brief Pillar**:
   - Every skill architecture must render an interactive, self-contained HTML visual brief written to `%TEMP%\<skill-name>-<timestamp>.html`.
   - Incorporates Mermaid DAG workflows, diagnostic scorecards, and anti-pattern defense matrices.

2. **The Mandatory Checkpoint Gate Pillar**:
   - Halts autonomous execution before modifying workspace code or committing artifacts.
   - Presents explicit review plan with `RequestFeedback: true` to confirm boundaries and design decisions.

3. **The Anti-Pattern Defense Pillar**:
   - Hardens the agent against known anti-patterns (e.g. Prompt Sprawl, Static Forking, Interactive Script Hangs).
   - Formatted strictly under `## Anti-Patterns` with `- **Name** — Description`.

---

## Vocabulary Cheat Sheet

- **Token Economics**: Calculating amortized prompt costs across multi-turn sessions to justify on-demand skill modularization ($>90\%$ token savings).
- **Two-Phase Validation**: Separating syntactic AST parsing (Phase 1) from semantic domain rule enforcement (Phase 2).
- **Local String Salvage**: Deterministically stripping markdown fences, extracting outermost JSON brackets, and repairing trailing commas without consuming model tokens.
- **Additive Configuration Lists**: Using `extra_*` keys in project overrides to append to default lists without wiping out base configurations.
- **SkillSpector Risk Bands**: 4-tier risk classification: SAFE ($\le 20$), CAUTION ($21-50$), HIGH ($51-80$), and CRITICAL ($81-100$).
- **Shu-Ha-Ri Completion Gates**: Binary, testable invariants that confirm stage completion before subsequent phases begin.

---

## Invariants & Pre-Flight Verification Checklist

- [ ] `SKILL.md` contains valid YAML frontmatter with `name:` and `description:` (<500 characters).
- [ ] `SKILL.md` body is bounded strictly under 500 lines (`line_budget_limit`).
- [ ] `CARD.md` uses single-pipe `│` borders and contains `SKILL:` tag identifier.
- [ ] `## Anti-Patterns` section declared with items formatted as `- **Name** — Description`.
- [ ] Bundled scripts configure standard streams to UTF-8 (`sys.stdout.reconfigure(encoding="utf-8")`).
- [ ] Zero interactive prompts (`input()`) in bundled Python scripts.
- [ ] Zero hardcoded machine absolute paths in bundled scripts.
- [ ] All reference documents in `references/` are linked with conditional trigger sentences in `SKILL.md`.
- [ ] `validate_skill.py` passes with zero failures.
- [ ] `harness skills validate` passes with zero errors.
