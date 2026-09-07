# Skill Summary Card: `developer-docs-architect`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:       developer-docs-architect                 │
│ Name:        developer-docs-architect                 │
│ Category:    integration_and_io / developer-docs       │
│ Invocation:  /developer-docs-architect                 │
│ Triggers:    "build API documentation",                │
│              "audit documentation", "diataxis gap",    │
│              "C4 architecture diagrams", "docs as code"│
│ Version:     1.1.0                                     │
│ Isolation:   in-process                                │
│ Provides:    "service.developer_docs_architect"        │
├────────────────────────────────────────────────────────┤
│ Target:      Architect, author, audit, and automate    │
│              technical documentation suites and C4     │
│              architecture blueprints.                  │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Documentation Architecture Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Intent & Taxonomy Framing** | Audit personas & classify documentation into Diátaxis quadrants | Diátaxis Coverage Matrix | `Taxonomy coverage gap matrix authored` |
| **2. Multi-View C4 Modeling** | Author Context, Container, and Component views in Mermaid.js | Mermaid C4 Architecture Diagrams | `3 C4 views authored with zero static PNGs` |
| **3. 2-Track API Blueprinting** | Author Track A onboarding guide and Track B 6-part endpoint references | API Reference & Error Catalog | `All endpoints implement 6-section anatomy` |
| **4. 4-Pass Editorial & GEO** | Refine tone, constrain bolding <=10%, and generate AI agent index | Editorial Report & llms.txt | `4-pass checklist signed off with llms.txt` |
| **5. Docs-as-Code Pipeline** | Bind OpenAPI specs, configure CI linter workflows, and verify sync | CI Workflow & Validation Report | `Docs-as-Code CI sync pipeline verified` |

---

## Authoritative Tooling Seams

```bash
# 1. AST Markdown & Editorial Linter (Bolding <=10%, Heading Hierarchy, 6-Section Anatomy)
python scripts/doc_linter.py <path> [--json] [--max-bolding 10]

# 2. OpenAPI 3.0 to Track B Markdown Synchronizer
python scripts/openapi_doc_sync.py --spec <spec.json> --out <docs_dir> [--json]
```

---

## Deep Reference Blueprints

- [`diataxis-taxonomy-guide.md`](references/diataxis-taxonomy-guide.md) — 4-quadrant taxonomy criteria and anti-conflation rules.
- [`c4-mermaid-blueprints.md`](references/c4-mermaid-blueprints.md) — Level 1–3 Mermaid templates with business translation tables.
- [`api-endpoint-anatomy-guide.md`](references/api-endpoint-anatomy-guide.md) — 6-section API anatomy and actionable error catalog taxonomy.

---

## Tri-Pillar Architecture Cheat Sheet

### 1. The Visual Brief (`%TEMP%` + Mermaid.js)
```html
<!-- Location: %TEMP%\developer-docs-architect-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto">
  <!-- Interactive Diátaxis Matrix & C4 System Blueprint -->
</body>
</html>
```

### 2. The Mandatory Checkpoint (`RequestFeedback: true`)
```markdown
# Implementation Plan
Set `RequestFeedback: true` in artifact metadata.
Agent MUST STOP and await explicit user approval before modifying documentation.
```

### 3. Explicit Anti-Patterns Defense Box
- **Wall-of-Jargon Syndrome**: Reject backend buzzwords without a user-facing outcome translation table.
- **Static Image Rot**: Ban PNG/SVG diagrams; enforce Diagrams-as-Code via fenced Mermaid.js blocks.
- **Generic Error Dumping**: Mandate full 6-part endpoint anatomy with actionable error remediation.
- **Taxonomic Conflation**: Separate tutorials, how-to guides, reference specs, and explanations.
- **Context-Orphaned Pages**: Ensure all pages declare prerequisites, dependencies, and environment bounds.
- **Drift Abandonment**: Maintain docs in Git alongside source code with automated CI pull request checks.

---

## Mandatory Invariants Checklist

- [ ] **Diátaxis Compliance**: Every page assigned to exactly one quadrant (Tutorial, How-To, Reference, Explanation).
- [ ] **Zero Static PNGs**: All architectural visualizations authored in code-based Mermaid.js diagrams.
- [ ] **6-Section Endpoint Anatomy**: Every API endpoint documents URL, auth, parameters, body, responses, and errors.
- [ ] **Bolding Ratio Guard**: Bold emphasis restricted to <=10% of total document volume (`scripts/doc_linter.py`).
- [ ] **AI-Agent Readiness**: Clean markdown heading hierarchy, explicit codeblock fences, and `llms.txt` index.
- [ ] **Docs-as-Code CI Gates**: OpenAPI spec committed and validated; documentation tested in pull requests.
