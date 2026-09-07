---
name: agent-skills-architect
description: Architect, specify, implement, test, and govern enterprise AI agent skills using open standards (agentskills.io, Google Cloud). Use when designing progressive disclosure skills, configuring runtime tool approval middleware, running CI linters, or running Google 2x2 continuous evals. Do not use for raw prompt formatting or simple script generation.
---

# Enterprise Agent Skills Architecture & Standards

`agent-skills-architect` is the enterprise engineering engine for designing, implementing, verifying, and governing production-grade AI agent skills. It operationalizes foundational standards from Daniel Warfield (loose constraint theory), Sergey Menshykh (agentskills.io / Microsoft Agent Framework), and Remigiusz Samborski (Google Cloud) into an end-to-end engineering discipline that eliminates **Context Flooding Monoliths**, **Snippet Abandonment**, and **Unbounded Script Elevation**.

See [CARD.md](CARD.md) for the companion summary card, 5-stage reference matrix, and quality checklist.
Consult `/agent-skill-sdlc` for Talele's prompt-to-skill SDLC and `/crafting-skills` for authoring guidelines.

---

## The 5-Stage Agent Skill Architecture Loop

```
[1. Intake & Bounds] ──► [2. Progressive Disclosure] ──► [3. Security & Approval]
                                                                  │
                                                                  ▼
[5. Continuous Evals & Gov] ◄── [4. Automated CI Linters] ◄───────┘
```

---

## 1. Intake & Boundary Engineering

Define the operational scope, activation triggers, and architectural boundaries:

1. **Apply Trigger Boundary Engineering**:
   - **Front-Load Trigger Action Verbs**: Position decisive operational verbs at the beginning of `description` (e.g. *Architect, specify, implement, test, and govern...*).
   - **Define Explicit Negative Boundaries**: Add mandatory `Do not use for...` deflection clauses to avoid stealing unrelated queries.
   - **Enforce Single-Intent Routing**: Ensure candidate descriptions exhibit >= 90% recall on positive prompts and 0% false positive rate on near-miss distractors.
2. **Execute the Skill vs. Workflow Decision Gate**:
   - *Choose an Agent Skill* when: The task requires dynamic, autonomous reasoning within an agent turn; domain expertise or local rulesets must be injected without locking execution into a rigid sequence.
   - *Choose a Workflow Graph (e.g. LangGraph / DAG Engine)* when: The task is deterministic, requires cross-turn rollback/resumption, or operates on strict, unchangeable state-machine transitions.

> **Completion criterion**: Operational boundaries agreed, frontmatter draft authored with explicit `Do not use for...` negative bounds, and skill vs. workflow decision validated.

---

## 2. Progressive Disclosure & Modality Selection

Eliminate the **Context Flooding Dilemma** by structuring domain knowledge across the three-tier progressive disclosure pattern and selecting the appropriate implementation modality:

1. **Partition into Three Progressive Disclosure Tiers**:
   - **Tier 1 (Discovery Catalog)**: Name and concise description (< 200 characters) registered in the system prompt. Incurring **zero token overhead** until dynamically invoked.
   - **Tier 2 (Instruction Body)**: The primary `SKILL.md` file (< 500 lines) loaded only when `load_skill(name)` is invoked.
   - **Tier 3 (Execution on Demand)**: Auxiliary reference tables, schemas, and executable scripts placed in `resources/` and `scripts/`, or exposed via remote MCP servers.
2. **Select the Skill Implementation Modality**:
   - **File-Based Skills**: Standalone directories containing `SKILL.md`, `resources/`, and `scripts/`. Best for portable, cross-platform domain knowledge.
   - **Code-Defined Skills**: Dynamic inline skills registered via builder APIs with inline lambda scripts and dynamic resource generators. Best for ephemeral runtime tasks.
   - **Class-Based Skills**: Strongly-typed classes using annotations (`@skill_resource`, `@skill_script`) and Dependency Injection (`IServiceProvider`). Best for enterprise microservices.
   - **MCP-Based Skills**: Tools and resources delegated to remote Model Context Protocol (MCP) endpoints with built-in IAM and authentication.

> **Completion criterion**: Content partitioned across 3 tiers, `SKILL.md` bounded under 500 lines, auxiliary data offloaded to `resources/`, and implementation modality selected.

---

## 3. Runtime Security & Tool Approval Middleware

Protect the agent harness by treating skills as untrusted third-party code and configuring defense-in-depth execution gates:

1. **Configure Tool Approval Middleware**:
   - Install `ToolApprovalMiddleware` in the agent execution pipeline.
   - Apply the **Read-Only Auto-Approval Rule** (`SkillsProvider.read_only_tools_auto_approval_rule`): automatically approves `load_skill` and `read_skill_resource` without pausing execution.
   - Enforce **Explicit Approval / Sandboxing for Mutating Scripts**: Calls to `run_skill_script` must either require user confirmation or run inside isolated subprocess sandboxes with pipe disposal invariants.
   - Test runtime policies directly with the middleware guard:
     ```bash
     python scripts/runtime_middleware_guard.py --tool run_skill_script --skill custom-skill
     ```
2. **Inject Runtime Application Context**:
   - Wire application services via Dependency Injection (`IServiceProvider`) to avoid hardcoding credentials or connection strings into markdown files.
   - Forward dynamic runtime arguments via `function_invocation_kwargs` / `**kwargs`.

> **Completion criterion**: Tool approval rules configured, read-only tools auto-approved, mutating scripts gated, and runtime DI wired.

---

## 4. Automated CI Check-In Gates

Assert that skills conform to enterprise production standards before merging into the catalog:

1. **Lint Frontmatter & Directory Layout**:
   - Validate YAML frontmatter delimiters, required fields (`name`, `description`), and kebab-case directory naming.
   - Verify line count budgets (`SKILL.md` < 500 lines, description < 350 characters).
2. **Automate Link Checking**:
   - Run automated link verification against every HTTP and markdown link to guarantee **0% 404s or hallucinated URLs**.
3. **Execute AI-Assisted Structural Checklist**:
   - Assert the presence of the three foundational craft pillars:
     1. **The Visual Brief** (%TEMP% HTML with Mermaid DAGs)
     2. **The Mandatory Checkpoint** (`RequestFeedback: true`)
     3. **Anti-Patterns** (`## Anti-Patterns` with `- **Name** — Description`)
   - Assert presence of co-located `CARD.md` with single-pipe ASCII borders.
4. **Execute Enterprise CI Linter**:
   - Run the bundled CI check-in linter against the target skill:
     ```bash
     python scripts/skill_ci_linter.py <path-to-skill>
     ```

> **Completion criterion**: Skill package passes all automated CI linters (`skill_ci_linter.py` exit code 0), link checkers show zero 404s, and structural checks pass with zero errors.

---

## 5. Continuous 2x2 Evals & Governance

Enforce Google's enterprise quality principle: **"Skills are living products, not one-off snippets."**

1. **Author the Evaluation Test Suite**:
   - Scaffold an evaluation suite based on [eval_matrix_template.json](resources/eval_matrix_template.json) defining baseline and skill-augmented prompt test cases.
2. **Execute the 2x2 Continuous Evaluation Matrix**:
   - Run test cases across target model tiers (Gemini 3.8 Flash, Claude 3.7 Sonnet, OpenAI o-series).
   - Execute the multi-case suite uplift calculator:
     ```bash
     python scripts/eval_uplift_calculator.py --suite resources/eval_matrix_template.json
     ```
   - Assert placement in the **DOMINANT_UPLIFT** quadrant (Accuracy Uplift >= 15%, Token Savings >= 30%). Reject skills in the **DEGRADED** quadrant.
3. **Establish Product Governance & Public Export**:
   - Assign dedicated skill owners responsible for upstream API drift and weekly regression jobs.
   - Configure export sanitization rules to strip internal credentials and private evals prior to public open-source release.

> **Completion criterion**: 2x2 eval matrix executed across full suite, DOMINANT_UPLIFT verified across target models, and long-term skill owner assigned.

---

## The Three Foundational Pillars

### 1. The Visual Brief
Before publishing or executing complex multi-stage skills, synthesize the operational workflow into a self-contained HTML brief in `%TEMP%` loading Tailwind CSS and Mermaid.js via CDN. Present the absolute clickable path to the user for decision-ready visual review.

### 2. The Mandatory Checkpoint
When executing high-leverage architectural modifications or forging new skills, always author an `implementation_plan.md` artifact with `RequestFeedback: true`. The agent must **STOP and wait** for explicit human confirmation before mutating files.

### 3. Explicit Anti-Patterns
Rigid behavioral boundaries must be maintained to prevent catastrophic failure modes.

---

## Anti-Patterns

- **Context Flooding Monolith** — Inlining large reference tables, exhaustive API specs, or multi-page documentation directly into `SKILL.md` or system prompts instead of using Tier 3 progressive disclosure (`resources/`).
- **Snippet Abandonment** — Publishing a skill as a one-off markdown document without CI linters, test cases, or designated product maintainers.
- **Unbounded Script Elevation** — Permitting `run_skill_script` to execute arbitrary local shell commands without subprocess isolation, pipe disposal invariants, or user approval.
- **Unevaluated Skill Claims** — Merging skills into the enterprise catalog without measuring Accuracy Uplift and Token Efficiency Uplift against baseline trajectories.
- **Graph Workload Misplacement** — Forcing rigid, deterministic state machines with rollback requirements into an agent skill rather than a dedicated workflow graph.
