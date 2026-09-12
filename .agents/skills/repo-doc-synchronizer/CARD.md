```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:        repo-doc-synchronizer                    │
│ Category:     documentation_and_governance             │
│ Invocation:   /repo-doc-synchronizer                   │
│ Triggers:     "audit docs", "update documentation",    │
│               "check doc coverage", "scaffold docs",   │
│               "create missing documentation"           │
│ Version:      1.0.0                                    │
│ Isolation:    subprocess                               │
│ Provides:     "service.doc_synchronizer"               │
├────────────────────────────────────────────────────────┤
│ Target:       Audit repository documentation coverage, │
│               detect drift against live code ASTs,     │
│               and author missing Diátaxis doc suites.  │
└────────────────────────────────────────────────────────┘
```

# Repository Documentation Synchronizer — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
| --- | --- | --- | --- |
| **1. Coverage Audit** | Scan Python modules via AST, count symbols, compute coverage % against threshold | `coverage_scorecard.json` | `Audit complete and coverage evaluated` |
| **2. Drift Inspection** | Inspect Markdown files for broken local file links and stale symbol signatures | `drift_report.json` | `Drift check complete with zero unlogged errors` |
| **3. Visual Brief & Review** | Render dark-mode Mermaid.js topology diagram and present implementation plan | `doc_brief.html` | `Visual brief rendered & user approval received` |
| **4. Scaffolding & Verification** | Scaffold Diátaxis markdown docs using live AST symbols and verify coverage | `doc_slice.md` / `*.md` | `Missing documentation authored and verified` |

---

## Input & Output Schema Specification

### Input Schema

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `root_dir` | string | Optional | Target repository or package root directory (default: `.`) |
| `min_coverage` | float | Optional | Minimum acceptable documentation coverage percentage (default: `80.0`) |
| `doc_type` | string | Optional | Diátaxis document type for scaffolding (`api`, `readme`, `howto`) |
| `module_path` | string | Optional | Specific Python module path to inspect or scaffold |
| `output_path` | string | Optional | Filepath for written JSON or Markdown artifacts |

### Output Schema

| Field | Type | Description |
| --- | --- | --- |
| `overall_coverage_pct` | float | Composite documentation coverage percentage |
| `passed` | boolean | True if overall coverage satisfies `min_coverage` threshold |
| `missing_docs_count` | integer | Number of modules lacking docstrings or dedicated documentation |
| `broken_links_count` | integer | Number of broken relative file links detected in markdown files |
| `scaffolded_path` | string | Output filepath of authored Diátaxis markdown documentation |

---

## Mandatory Invariants Checklist

- [ ] **AST Derivation Invariant**: All generated API references and symbol tables must be derived from live Python AST trees, never hallucinated.
- [ ] **Code Block Link Isolation**: Link checkers must strip code blocks and use negative lookarounds (`(?<!\[)` and `(?!\])`) on backticks before validating relative links to prevent false positives (Rule 47).
- [ ] **Runtime Store Exclusion**: Link and coverage scanners must exclude runtime state directories (`.harness`, `.system_generated`, `test_ingested_plugins`).
- [ ] **Relative Link Invariant**: All cross-document and cross-skill links must use relative paths rather than workspace-absolute `file:///` URIs.
- [ ] **Human-in-the-Loop Checkpoint**: The agent must generate a coverage audit scorecard and receive user approval before mutating or creating files.
