---
name: token-economizer
description: Control coding agent token waste through experience-driven micro-skills lifecycle, empirical evidence-based tool pruning, and 3-tier failure-loop turn guard intervention. Do not use for generic prompt formatting, untracked string concatenation, or static token budgeting.
---

# TokenEconomizer: Experience-Driven Black-Box Cost Control for Coding Agents

`token-economizer` implements black-box cost control for autonomous coding agents, founded on UC Berkeley and Microsoft Research principles (Aaron J. Li et al., arXiv:2610.22732). It learns from the sessions an agent has already executed in a repository, and applies that accumulated experience to eliminate recurring token waste across subsequent sessions without modifying agent internals or compromising task success rates.

See [CARD.md](CARD.md) for the companion summary card, stage progression table, and mandatory invariants checklist.
Consult [config.default.yaml](config.default.yaml) for operational parameters and algorithmic thresholds.

---

## The Three Foundational Pillars

### 1. Micro-Skills Lifecycle & Asymmetric Contradiction Eviction
Repositories contain persistent operational realities: project-specific test runners (`python -m pytest` vs bare `pytest`), missing compiler flags, generated file paths, or required environment variables. Instead of forcing agents to rediscover these facts each session through expensive trial-and-error spirals, micro-skills promotes verified environmental facts into the prompt prefix:
- **Candidacy**: Proposed by an environmental fact detector following a failing command recovered by a successful one, or via periodic offline transcript distillation review every $k = 3$ sessions.
- **Promotion ($K = 3$)**: A fact is promoted from `CANDIDATE` to `ACTIVE` only after confirmation across $K = 3$ distinct sessions. For code facts, promotion requires confirmation across distinct edited files (`_drifted_confirms()`) to prevent overfitting to a single file coincidence.
- **Asymmetric Eviction ($\lambda = 5.0, \gamma = 0.8$)**: Active facts decay over time with recency factor $\gamma = 0.8$ per task. Contradictions are penalized with an asymmetric penalty $\lambda = 5.0$. If the weighted score drops below $0.0$, or a high-stakes fact encounters a single clean contradiction (`HARD_KILL=True`), it is retired immediately.
- **The Firing Gate ($\ge 40\%$)**: Even `ACTIVE` facts are only injected into prompt context if their historical firing rate clears $\text{FIRE\_GATE} \ge 0.40$ over at least 4 exercised sessions, guaranteeing zero prompt bloat.

### 2. Empirical Evidence-Based Tool Pruning & Work-Surface Invariants
Every loaded tool's complete JSONSchema parameter description is transmitted and billed on every single conversational turn. Across repositories, agents load massive monolithic toolboxes where only a small fraction are ever used:
- **Protected Work-Surface**: Core primitives (`read_file`, `edit_file`, `run_command`, `write_file`) are strictly protected and never dropped.
- **Inapplicable Tools**: Tools known a priori to be irrelevant to the repository domain (e.g. Jupyter notebook or web browsing tools in a pure CLI backend repo) are excluded by construction.
- **Evidence-Based Thresholding ($p=10, m=2, s=5$)**: A tool is proposed for pruning if it remains loaded but unused across $p=10$ prompts spread across at least $m=2$ sessions, or across $s=5$ sessions of any length.
- **Fast Restoration**: A single explicit invocation or restoration signal immediately returns pruned tools to active scope on subsequent turns.

### 3. 3-Tier Failure-Loop Intervention & Non-Destructive Mirroring
When coding agents get stuck in failure loops, they waste massive context windows repeating identical tool calls or thrashing edits:
- **Tier 0 (Free Gate)**: Only inspect trajectory if $\text{turns} \ge 18$ and $\text{error\_outputs} \ge 8$. Evaluated with zero token overhead.
- **Tier 1 (Strict Heuristic Conjunction)**: A trajectory is deemed stuck if and only if a strict conjunction of 4 signals is met:
  1. High Edit Churn ($\ge 4$ edits to one file) OR High File Scatter ($\ge 3$ distinct files edited).
  2. Sustained Errors ($\ge 6$ error tool returns).
  3. Stagnation ($\ge 20\%$ of failure outputs are exact repetitions of an earlier failure).
  4. Envelope Overflow (current turn count exceeds $1.25\times$ the repository's p90 resolved-task envelope).
- **Tier 2 (Judge & Hard Backstop)**: If the gate triggers but heuristics are ambiguous, an optional lightweight judge model is queried. However, if a turn exceeds $2.5\times$ the resolved-task envelope, it aborts regardless of judge verdict to prevent catastrophic token drain.
- **Non-Destructive Mirroring Nudge**: The first intervention is never an abort; it delivers an objective redirect mirroring the agent's recent repetitive actions back to it without outside bias.

---

## Architecture & Data Flow

```
┌────────────────────────────────────────────────────────┐
│                   Agent Session Log                     │
│        (Claude Code / Codex / Copilot / Pi / JSONL)    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│               tokeneconomizer.trace                    │
│      load_trajectory() / tool_usage() / parse_catalog() │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│           tokeneconomizer.domain.DomainAdapter         │
└──────┬────────────────────┼────────────────────┬───────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Micro-Skills │     │ Tool Pruning │     │  Turn Guard  │
│  Lifecycle   │     │  Thresholds  │     │ 3-Tier Loop  │
│ (K=3, γ=0.8, │     │ (p=10, m=2,  │     │ Intervene &  │
│    λ=5.0)    │     │     s=5)     │     │ 2.5x Backstop│
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│          tokeneconomizer.ledger & pricing              │
│       (Unified Token Accounting & Cost Defense)        │
└────────────────────────────────────────────────────────┘
```

---

## Anti-Patterns

- **Speculative Fact Bloat** — Injecting single-session observations into system prompts without drift verification across distinct tasks.
- **Symmetric Forgetting** — Treating failure contradictions with equal weight as confirmations ($\lambda=1.0$), which preserves stale, broken repository instructions.
- **Unprotected Core Pruning** — Dropping critical read, edit, or command primitives due to temporary inactivity.
- **Premature Halting** — Aborting productive, challenging agent tasks where error signatures are actively evolving and code edits are progressing.
- **Unchecked Loop Spirals** — Allowing unbounded model turns where identical error traces repeat without a hard circuit-breaker backstop ($2.5\times$).
- **Vendor-Locked Pruning** — Hardcoding token optimization hooks into proprietary agent CLIs without abstracting through `DomainAdapter` and `Stage`.

