# Skill Summary Card: `agent-skills-architect`

```
┌────────────────────────────────────────────────────────┐
│                  SKILL SUMMARY CARD                    │
├────────────────────────────────────────────────────────┤
│ SKILL:       agent-skills-architect                    │
│ Category:    software_engineering / agent-skills       │
│ Invocation:  /agent-skills-architect                   │
│ Trigger:     "architect agent skill",                  │
│              "progressive disclosure skill",           │
│              "runtime tool approval middleware",       │
│              "google 2x2 continuous evals",            │
│              "enterprise agent skill governance"       │
│ Version:     1.0.0                                     │
│ Provides:    "enterprise_agent_skills_architecture"    │
├────────────────────────────────────────────────────────┤
│ Target:      Architect, specify, implement, test, and  │
│              govern enterprise AI agent skills using   │
│              open standards (agentskills.io, Google).  │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Agent Skill Architecture Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Intake & Bounds** | Define operational scope, triggers, negative bounds, skill vs workflow | Trigger matrix & negative bounds | Recall >= 90%, false-positives 0%, negative bounds defined |
| **2. Progressive Disclosure** | Partition into 3 tiers; select modality (File, Code, Class, MCP) | Modularized directory & `resources/` | `SKILL.md` < 500 lines, tables offloaded to `resources/` |
| **3. Security & Approval** | Configure `ToolApprovalMiddleware`, auto-approve read-only, sandbox scripts | Configured approval rules & DI | Read-only auto-approved, mutating scripts gated |
| **4. Automated CI Linters** | Validate frontmatter, check 100% of links, verify craft pillars | CI validation report | Zero linter errors, zero 404s/broken links |
| **5. Continuous Evals** | Execute 2x2 eval matrix (Accuracy vs Efficiency uplift), assign owner | 2x2 Evaluation Report | Placed in `DOMINANT_UPLIFT` quadrant across target models |

---

## The Three Pillars Cheat Sheet

### 1. The Visual Brief (Temp HTML + Mermaid)
```html
<!-- Location: %TEMP%\agent-skills-architect-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto">
  <!-- Mermaid DAG & 2x2 Evaluation Matrix -->
</body>
</html>
```

### 2. The Mandatory Checkpoint (`RequestFeedback: true`)
```markdown
# Implementation Plan
Set `RequestFeedback: true` in artifact metadata.
Agent MUST STOP and wait for explicit human approval before mutating files.
```

### 3. Explicit Anti-Patterns Box
- **Context Flooding Monolith**: Inlining large reference tables into `SKILL.md` instead of using `resources/`.
- **Snippet Abandonment**: Creating one-off skills without ongoing ownership or automated CI regression runs.
- **Unbounded Script Elevation**: Allowing script execution without tool approval middleware or subprocess sandboxing.
- **Unevaluated Skill Claims**: Committing skills without measuring accuracy and efficiency uplift against baseline agents.
- **Graph Workload Misplacement**: Forcing rigid deterministic state machines into loose-constraint skills.

---

## Verification & Quality Checklist

- [ ] **Frontmatter Compliance**: Contains `name` and `description` with front-loaded action verbs and negative bounds.
- [ ] **Line Budget**: `SKILL.md` is strictly under 500 lines; system prompt metadata is under 200 characters.
- [ ] **Progressive Disclosure**: Detailed conversion tables, schemas, and scripts live in `resources/` and `scripts/`.
- [ ] **Security Middleware**: `read_only_tools_auto_approval_rule` enabled; mutating scripts gated or sandboxed.
- [ ] **Automated CI Validation**: Passes `harness skills validate` and `skill_ci_linter.py` with zero errors.
- [ ] **2x2 Continuous Evals**: Baseline vs skill test suite (`eval_uplift_calculator.py --suite`) confirms `DOMINANT_UPLIFT`.
- [ ] **Product Ownership**: Designated skill owner identified for long-term API maintenance.
