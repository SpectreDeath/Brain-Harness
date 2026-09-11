---
name: agent-skill-sdlc
description: Design, configure, validate, test, and audit production-grade AI agent skills across their full lifecycle (v1-v5). Implement zero-fork config, two-phase validators, and SkillSpector audits. Do not use for generic prompt writing.
---

# Agent Skill SDLC: Production Engineering & Lifecycle Architecture

`agent-skill-sdlc` is the operational engineering framework for creating, testing, configuring, and maintaining robust, production-grade AI agent skills. It operationalizes foundational principles from Sarvesh Talele, Obum, and Vineeth Pawar into a disciplined 5-phase software development lifecycle that eliminates **Prompt Sprawl**, **Static Fork Nightmares**, and **Parse Fragility**.

See [CARD.md](CARD.md) for the companion summary card, 5-phase matrix, and vocabulary cheat sheet.
Consult `/crafting-skills` for craft guidelines, `/book-to-skill-forge` for literature extraction, and `/epistemic-isnad-audit` for provenance verification.

---

## The 5-Phase Agent Skill SDLC Loop

```
[1. Trigger Engineering] ──► [2. Config Decoupling] ──► [3. Bundled Scripts & Salvage]
                                                                │
                                                                ▼
[5. Security Audit & Graph] ◄── [4. Two-Phase Validation & Repair]
```

---

## 1. Trigger Engineering & System Architecture

Design high-precision activation boundaries and decoupled module interfaces:

1. **Apply Talele's 4 Trigger Principles**:
   - **Name Target Operations Explicitly**: Specify concrete nouns and verbs (e.g. `scaffold agent skill`, `validate skill schema`).
   - **Front-Load Trigger Verb Phrases**: Position action phrases at the beginning of descriptions to maximize routing attention weights.
   - **Define Negative Boundaries**: Add explicit `Do not use for...` clauses to deflect irrelevant queries.
   - **Measure Trigger Separation**: Test candidate descriptions against positive queries and near-miss distractor prompts.
2. **Evaluate Graduation Triggers**:
   - When deciding whether an ad-hoc prompt should be extracted into a modular skill, evaluate the token economics and graduation thresholds detailed in [prompt-to-skill-heuristics.md](references/prompt-to-skill-heuristics.md).
3. **Partition Problem Scope**:
   - Split large monoliths into composable, single-responsibility skills bounded strictly under 500 lines.

> **Completion gate**: `Trigger matrix validated` (positive recall $\ge 90\%$, near-miss false-positive rate $0\%$, negative boundary defined).

---

## 2. Configuration & Deep-Module Decoupling

Decouple skill defaults from repository-specific customization without forking:

1. **Scaffold Default Configuration**:
   - Author `config.default.yaml` containing sensible base parameters, line limits, and client targets.
2. **Implement 3-Tier Layered Precedence**:
   - Precedence: Project Override (`.agents/skills.config.yaml`) $\rightarrow$ Skill Default (`config.default.yaml`) $\rightarrow$ Hardcoded Fallback.
   - Support additive lists via the `extra_*` prefix (e.g. `extra_supported_clients`).
3. **Verify Configuration Resolution**:
   - Execute the configuration resolution utility to verify precedence merges:
     ```bash
     python scripts/resolve_config.py <skill-name> --project-root . --print-sources
     ```
   - For an end-to-end zero-fork customization walkthrough, see [README.md](examples/git-commit-formatter/README.md).

> **Completion gate**: `Config resolution clean` (`resolve_config.py` resolves cleanly across all tiers with zero unmerged conflicts).

---

## 3. Bundled Scripts & Local Salvage Loops

Equip skills with deterministic execution scripts and local model-output repair utilities:

1. **Enforce Script Hygiene**:
   - All scripts must declare PEP 723 metadata blocks specifying required runtime and dependency bounds.
   - Configure standard streams to UTF-8 (`sys.stdout.reconfigure(encoding="utf-8")`) to prevent Windows codec crashes.
   - Eliminate interactive calls (`input()`) to prevent proactor freezes.
   - Resolve all filesystem paths dynamically using relative anchors; never hardcode absolute paths.
2. **Implement Local String Salvage**:
   - Prior to paying LLM tokens for reprompts on parse failure, run fast local string salvage:
     1. Strip markdown code fences (````json ... ````).
     2. Slice text between outermost `{...}` or `[...]`.
     3. Remove trailing commas before closing braces/brackets (`,\s*([}\]])` $\rightarrow$ `\1`).
   - Test salvage on raw model outputs:
     ```bash
     python scripts/validate_skill.py --salvage raw_output.txt
     ```
3. **Reference Implementations**:
   - Review the complete slide deck builder evolution from prompt to script-coupled tool in [README.md](examples/deck-builder/README.md).

> **Completion gate**: `Scripts verified non-interactive` (zero `input()` calls, relocatable paths, local string salvage operational).

---

## 4. Two-Phase Validation & Behavioral Verification

Enforce rigorous syntactic and semantic validation with bounded repair loops:

1. **Two-Phase Diagnostic Architecture**:
   - When designing schema validation rules or configuring repair loop circuit breakers, consult [two-phase-validation-patterns.md](references/two-phase-validation-patterns.md).
   - **Phase 1 (Syntactic)**: YAML frontmatter validity, strict kebab-case naming, description length [20, 500], line budget limit ($\le 500$ lines), and sequential heading hierarchy.
   - **Phase 2 (Semantic)**: CARD.md single-pipe borders (`│`), ASCII header tags, binary completion gates for all stages, anti-patterns formatting, and reference trigger coverage.
2. **Execute Diagnostic Validation**:
   - Run the two-phase validator against the target skill package:
     ```bash
     python scripts/validate_skill.py .agents/skills/<skill-name> --json
     ```
3. **Path-Targeted Repair & Circuit Breaker**:
   - On semantic validation failures, send only targeted delta payloads `{issue.path: issue.message}` back to the model.
   - Enforce a hard circuit-breaker stop at 3 repair attempts.

> **Completion gate**: `Two-phase validation passes` (`validate_skill.py` exits 0 with zero failed diagnostic checks).

---

## 5. Security Auditing & Pre-Flight Graduation

Audit dangerous operations, evaluate supply-chain risks, and index the skill into the knowledge graph:

1. **Execute SkillSpector 70-Pattern Security Audit**:
   - Scan bundled scripts and prompt text across 4 weighted dimensions: Dangerous System Calls (30%), Network Exfiltration (30%), Filesystem Mutation (20%), and Credential Access (20%).
   - Consult the risk matrix and CI integration patterns in [security-and-skillspector.md](references/security-and-skillspector.md).
2. **Verify Risk Threshold**:
   - Assert that aggregate Security Risk Score $\le 20$ (**SAFE** band). If score is $>20$, require explicit manual review seam before release.
3. **Validate & Index into Harness Graph**:
   - Run the Harness platform validation and graph indexers:
     ```bash
     harness skills validate .agents/skills/<skill-name>
     harness skills graph
     ```
4. **Register in Context Map**:
   - Update `CONTEXT-MAP.md` under the appropriate domain.

> **Completion gate**: `Pre-flight score <= 20` (SkillSpector score $\le 20$, `harness skills validate` passes, skill indexed in graph).

---

## The Visual Brief Pillar

Every skill synthesis session must generate an interactive, self-contained HTML visual brief:

1. **Target File Location**:
   - Write to `%TEMP%\agent-skill-sdlc-<timestamp>.html` (Windows) or `/tmp/agent-skill-sdlc-<timestamp>.html` (Unix).
2. **Content & Theme**:
   - Sleek dark theme (`#0d1117`) loading Tailwind CSS and Mermaid.js via CDN.
   - Render a **Lifecycle Flowchart DAG** displaying phase progression and completion gates.
   - Render the **Diagnostic Evaluation Scorecard Table** detailing pass/fail status across syntactic and semantic rules.
   - Render the **Anti-Pattern Defense Matrix**.
3. **Delivery**:
   - Present the clickable file path to the user.

---

## Mandatory Checkpoint Gate Pillar

Prevent premature execution and unreviewed state mutations:

1. Present draft `implementation_plan.md` detailing:
   - Target skill name and directory path.
   - Bounded 5-phase progression and binary completion gates.
   - Tool couplings, scripts, and configuration schemas.
   - Explicit anti-patterns and defense invariants.
2. Set `RequestFeedback: true` in artifact metadata.
3. **STOP and wait** for explicit user review and approval before creating or modifying code files.

---

## Axis 3 Coaching Rubric & Diagnostic Scorecard

| Dimension | Evaluation Question | Passing Gate |
|---|---|---|
| **Trigger Separation** | Can the router distinguish this skill from related tools without confusion? | Description front-loaded with specific verbs and explicit negative boundary. |
| **Configurability** | Can a developer adjust parameters without editing `config.default.yaml`? | Layered 3-tier config with additive `extra_*` lists supported. |
| **Determinism** | Are complex multi-step transformations backed by executable code? | Bundled Python scripts with PEP 723 metadata and UTF-8 streams. |
| **Error Resilience** | Does the skill recover gracefully from malformed LLM responses? | Two-phase validation with local string salvage and path-targeted repair. |
| **Security Posture** | Are bundled scripts safe to execute in unattended environments? | Zero `input()` calls, relocatable paths, SkillSpector score $\le 20$. |

---

## Anti-Patterns

- **Prompt Sprawl** — Inlining thousands of lines of instructions into system prompts rather than packaging into modular, on-demand skills.
- **Static Fork Nightmare** — Forking entire third-party skill repositories just to customize a single setting instead of using layered configuration overrides.
- **Vague Description Syndrome** — Authoring generic trigger descriptions that lead to unpredictable LLM activation rates and routing ambiguity.
- **General Knowledge Restatement** — Wasting token budget explaining domain facts the model already knows instead of focusing on deterministic workflows and edge cases.
- **Prose-Only Procedure** — Describing operational procedures entirely in natural language text without deterministic verification scripts.
- **Naive Full-Reprompt Retry** — Resending full agent prompt context on JSON validation failure instead of local string salvage and path-targeted repair.
- **Interactive Script Hang** — Bundling scripts that invoke blocking input prompts, causing agent proactor transports to freeze indefinitely.
- **Absolute Path Brittleness** — Hardcoding user-specific machine absolute paths in skill scripts, causing failures across developer workstations and CI runners.
- **Unscanned Third-Party Skills** — Ingesting external community skills into the workspace catalog without automated SkillSpector security auditing.
- **Unchecked Allowed-Tools Grant** — Granting broad tool execution privileges in frontmatter without runtime least-privilege verification.
