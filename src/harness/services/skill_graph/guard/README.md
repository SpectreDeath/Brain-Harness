# Skill Graph Guard

The `harness.services.skill_graph.guard` package implements structural invariant enforcement, AST scanning, and reachability verification for skill graph topologies.

---

## Architectural Invariants

- **Strict Reachability (`Rule 55`)**: Disallows synthesized fake edges between disconnected skill nodes.
- **Slotted Dataclasses (`Rule 12`)**: Guard invariants and proposal models declare `slots=True` and `frozen=True`.

---

## Module Reference

| Module | Core Classes / Symbols | Description |
|---|---|---|
| [`guard.py`](guard.py) | `SkillGraphGuard` | Primary validation guard verifying skill DAG reachability and schema conformance. |
| [`ast_scanner.py`](ast_scanner.py) | `SkillASTScanner` | AST-level symbol inspector extracting executable bindings and imports. |
| [`invariants.py`](invariants.py) | `GraphInvariant`, `verify_invariants` | Slotted rule assertions checking graph health. |
| [`rules.py`](rules.py) | `ReachabilityRule`, `AcyclicityRule` | Specialized DAG topology rules. |
| [`formatter.py`](formatter.py) | `format_guard_diagnostics` | Diagnostic formatter rendering ASCII/JSON violation reports. |
| [`proposals.py`](proposals.py) | `GraphRepairProposal` | Repair proposal structures for broken topological edges. |

