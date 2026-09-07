# Prompt-to-Skill Graduation Heuristics & Token Economics

## Overview & The Problem of Prompt Sprawl

As agent workflows grow in sophistication, developers frequently succumb to **Prompt Sprawl**—inlining lengthy, multi-page procedural instructions directly into system prompts or conversation context. While convenient during initial experimentation, prompt sprawl imposes severe compounding penalties:

1. **Context Window Degradation**: Large system prompts consume high percentages of available attention heads, diluting the agent's adherence to immediate task goals.
2. **Economic Waste**: Every turn in a 50-turn conversation pays the token tax of the static prompt repeatedly ($N \times \text{prompt\_tokens}$).
3. **Absence of Determinism**: Purely prompt-based procedures lack deterministic verification gates, reproducible unit tests, and runtime tool sandboxing.

---

## Token Economics & Amortized Cost Analysis

Consider an agent specialized in generating slides, generating git commits, or validating code. 

$$\text{Session Cost} = \sum_{t=1}^{T} \left(C_{\text{in}} \cdot S_t + C_{\text{out}} \cdot O_t\right)$$

Where:
- $T$ = Number of conversation turns (e.g. 50 turns).
- $S_t$ = Input tokens at turn $t$.
- $C_{\text{in}}, C_{\text{out}}$ = Cost per input/output token.

If a 3,000-token prompt is baked into the system prompt across 50 turns, that prompt is transmitted and billed 50 times:
$$\text{Static Cost} = 50 \times 3,000 = 150,000 \text{ tokens}$$

In contrast, under the **Skill Architecture**:
1. Only the 60-token description lives in the routing index.
2. The skill body is loaded dynamically **only when triggered** (e.g., 2 turns).
$$\text{Skill Cost} = (50 \times 60) + (2 \times 3,000) = 3,000 + 6,000 = 9,000 \text{ tokens}$$

**Net Savings**: $>94\%$ reduction in token expenditure, with zero context dilution on unrelated turns.

---

## The Four Graduation Triggers

Graduate an ad-hoc prompt or conversation instruction into a formal Agent Skill when any of the following four triggers are reached:

| Trigger | Threshold | Rationale |
|---|---|---|
| **1. Line Threshold** | $>100$ lines of instructions | Beyond 100 lines, LLMs exhibit selective instruction following; modular skills partition procedures into enforceable phases. |
| **2. Multi-Turn Frequency** | $\ge 3$ turns per session | When a task repeats across turns or user sessions, dynamic on-demand loading prevents paying the prompt tax continuously. |
| **3. Tool & Script Coupling** | Requires programmatic logic | When a task requires deterministic calculations, format conversions, or validation scripts (e.g. `pptx` generation, AST parsing). |
| **4. Reusability Across Tasks** | Multi-domain / multi-repo | When the workflow represents a general capability (e.g., commit formatting, PR review, security audit) needed across multiple projects. |

---

## The 5-Version Evolutionary Lifecycle (v1 → v5)

Every mature agent capability progresses through five distinct evolutionary stages:

```
v1: Prompt Snippet   ──►  v2: Ad-Hoc Markdown   ──►  v3: Bundled Skill
(Inline system msg)       (Local instructions)       (Scripts + Assets)
                                                            │
                                                            ▼
v5: Multi-Engine Skill ◄──  v4: Validated Tool-Coupled
(Cross-client standard)      (Two-phase tests + Gates)
```

### Version 1: Prompt Snippet
- **Characteristics**: Pasted directly into the chat box or user prompt.
- **Limitations**: Ephemeral, manual copy-pasting, zero versioning, non-reproducible.
- **Transition Gate**: User uses it more than twice $\rightarrow$ extract to file.

### Version 2: Ad-Hoc Markdown Instruction
- **Characteristics**: Saved as `instructions.md` or `.prompt` file in workspace.
- **Limitations**: No parameterization, no schema validation, prose-only without verification.
- **Transition Gate**: Exceeds 100 lines or requires external tools $\rightarrow$ scaffold skill package.

### Version 3: Bundled Skill (Scripts & Prompts)
- **Characteristics**: Placed in `.agents/skills/<skill-name>/` with `SKILL.md` and `scripts/`.
- **Strengths**: Deterministic python execution, isolated dependencies, versioned alongside code.
- **Transition Gate**: Complex outputs fail parsing or require custom configs $\rightarrow$ add validation & config.

### Version 4: Validated Tool-Coupled Skill
- **Characteristics**: Layered `config.default.yaml`, two-phase validation (`validate_skill.py`), local string salvage, and binary completion gates.
- **Strengths**: Hard failure boundaries, automated self-repair, zero manual babysitting.
- **Transition Gate**: Ready for team or multi-client distribution $\rightarrow$ security audit & packaging.

### Version 5: Multi-Engine Distributed Skill
- **Characteristics**: Audited via SkillSpector (Risk Score $\le 20$), cross-client compatible (`claude-code`, `antigravity`, `cursor`, `vscode`), indexed in central Skill Knowledge Graph.
- **Strengths**: Enterprise governance, continuous pre-flight verification, zero-fork customizability.
