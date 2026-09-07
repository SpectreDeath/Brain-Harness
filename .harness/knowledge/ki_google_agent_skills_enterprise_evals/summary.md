# Google Enterprise Agent Skills: Continuous Evals & Product Governance

**ID:** `ki_google_agent_skills_enterprise_evals`  
**Category:** `agent_orchestration`  
**Origin:** Remigiusz Samborski (*Behind the scenes: How we build, test, and scale Google Agent Skills*, Google Cloud)  
**Provenance Lineage:** Published September 2026.

## Executive Summary
As agent skill repositories scale from ad-hoc developer experiments to enterprise infrastructure (e.g. Google Agent Skills), open-source repositories face severe quality collapse without automated governance. A poorly authored skill with vague instructions, broken links, or hallucinated APIs degrades entire multi-agent swarms.

Google establishes the core architectural axiom: **"Skills are living products, not one-off snippets."** To maintain enterprise quality at scale, skills require automated check-in linters, continuous 2x2 multi-model evaluation matrices, and explicit product ownership.

---

## Core Enterprise Principles

### 1. "Skills Are Products, Not Snippets"
- **Repo Maintainers**: Oversee global repository health, CI check-in pipelines, schema rules, and architectural standards.
- **Skill Owners**: Maintain designated skills long-term, updating instructions when upstream APIs change and fixing performance regressions detected during weekly evaluation runs.
- **Public Export Sanitization**: Skills are developed and continuously evaluated internally; an automated export pipeline strips internal proprietary evaluation suites, metadata, and IAM credentials before publishing clean open-source packages.

### 2. Automated Check-In CI/CD Pipeline
Every skill submitted to the catalog must pass automated CI check-in gates before merging:
1. **Linters**: Validate YAML frontmatter schema, strict naming conventions, line count budgets, and standardized directory layout.
2. **Link Checkers**: Execute HTTP HEAD/GET probes against every URL in the skill to guarantee 0% 404s or hallucinated URLs.
3. **AI-Assisted Checklists**: Automated semantic checks verifying required structural sections (Visual Briefs, Mandatory Checkpoints, Anti-Patterns).

### 3. The 2x2 Continuous Evaluation Matrix
Authors must provide an evaluation test suite containing prompt sets and scoring rubrics. Automated jobs compare the performance of agents **with the skill** vs. **without the skill (baseline)** across two core dimensions:

```
                      ▲ Accuracy Uplift (Quality & Completion Rate)
                      │
   Quality-Dominant   │    DOMINANT UPLIFT (Target)
   [High Quality,     │    [High Quality Uplift,
    Higher Cost]      │     High Token/Time Savings]
 ─────────────────────┼──────────────────────────────► Efficiency Uplift
                      │                                (Tokens & Latency)
      DEGRADED        │    Cost-Dominant
   [Worse Quality,    │    [Slight Quality Drop,
    Higher Cost]      │     Massive Token Savings]
                      │
```

- **Dimension 1: Accuracy Uplift**:
  $$\Delta \text{Accuracy} = \text{Score}_{\text{with\_skill}} - \text{Score}_{\text{baseline}}$$
- **Dimension 2: Efficiency Uplift**:
  $$\Delta \text{Tokens} = \frac{\text{Tokens}_{\text{baseline}} - \text{Tokens}_{\text{with\_skill}}}{\text{Tokens}_{\text{baseline}}} \times 100\%$$

Runs are repeated across multiple agent harnesses and model tiers to ensure statistically significant proof of value.

---

## Architectural Invariants
1. **2x2 Uplift Invariant**: A skill cannot be merged into the enterprise catalog if it falls in the Degraded quadrant across target model tiers.
2. **Link Invariant**: Zero tolerance for broken or unreachable links in skill markdown documents.
3. **Remote MCP Preference**: Skills requiring tool execution should prioritize remote Model Context Protocol (MCP) servers with built-in IAM and auth governance over raw local shell scripts.
