```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: architecture-deepening-workflow                               │
│ Category: developer_tooling / architecture                           │
│ Version: 1.0.0                                                       │
│ Invocation: /architecture-deepening-workflow                         │
│ Triggers: "deepen architecture", "deepening cycle", "refactor monolith",│
│           "decompose hotspot", "run deepening workflow"              │
│ Requires: "monolith-decomposition-engine", "adversarial-agent-verifier"│
│ Target: 7-phase cycle: scan -> map -> factor -> verify -> brief -> push│
└──────────────────────────────────────────────────────────────────────┘
```

# Architecture Deepening Workflow — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Phase 1: Hotspot Mining** | Scan & rank files > 200 LOC | `scan_results.json` | Top candidates identified & noise pruned |
| **Phase 2: Seam Analysis** | Map AST callers, imports & Click groups | Seam Architecture Map | Callers & IoC keys isolated |
| **Phase 3: Subpackage Factoring** | Partition into submodules $\le 200$ LOC | Modular Subpackage | All submodules strictly $\le 200$ LOC (Rule 11) |
| **Phase 4: Contract Testing** | Author contract tests & check ruff | `test_*_decomposition.py` | 100% test pass rate & 0 ruff errors |
| **Phase 5: Visual Master Brief** | Generate standalone dark HTML brief | `%TEMP%\architecture-review-*.html` | Clickable HTML brief generated |
| **Phase 6: Regression Gate** | Run full cumulative regression suite | Regression Task Log | 1,000+ tests pass with 0 regressions |
| **Phase 7: Secure Git Push** | Stage cycle files & push with redaction | Git Commit / Origin Main | Pushed with Rule 15 token redaction |

---

## Mandatory Invariants Checklist

- [ ] **Strict Submodule Bounds**: Every single decomposed file must not exceed 200 lines (Rule 11).
- [ ] **Slotted & Frozen Dataclasses**: Internal state and check models must declare `slots=True, frozen=True` (Rule 12 & 43).
- [ ] **Click Single-Source Consolidation**: CLI command groups must register all subcommands in a single co-located block (Rule 6).
- [ ] **Rule 58 Single-Seam Resolver**: Subpackages must expose `resolve_*()` with IoC container resolution and fallback.
- [ ] **Rule 45 Plugin Singleton**: Plugin entrypoints must export `plugin = MyPlugin()` at module level.
- [ ] **Rule 15 Token Redaction**: Remote git pushes must execute via isolated runner scripts with in-memory token redaction.
- [ ] **Untracked File Isolation**: Never stage, modify, or delete untracked external files (e.g., GEV artifacts).
