## Dynamic 5D Compute Complexity & Reasoning Budget Escalation

### Discovery
Audits of large heterogeneous repositories or multi-agent swarms frequently experience context blowout, timeout drops, and shallow reasoning when dispatched with fixed, static model thinking budgets.

Brain Harness implements dynamic 5D complexity scoring across 5 orthogonal axes:
- **Ambiguity**: Precision of task boundary and domain specifications.
- **Span**: Breadth of monorepo package ecosystems, plugin count, and file volume.
- **Depth**: Logical complexity, AST transformation depth, transaction isolation, and recursive pathfinding.
- **Rigor**: Density of verification gates, test suites, and strict behavioral invariants.
- **Concurrency**: Density of async loops, subprocess sandbox pipes, and multi-agent thread DAGs.

### Architectural Invariant
When the composite score:
$$	ext{Composite} = rac{	ext{Ambiguity} + 	ext{Span} + 	ext{Depth} + 	ext{Rigor} + 	ext{Concurrency}}{5} \ge 0.75$$

The engine activates **Rule 25 Autonomic Escalation**:
1. Automatically locks model reasoning budget to **High** (e.g. Gemini 3.8 Flash High thinking / Claude 3.7 Sonnet 16k thinking).
2. Scales async subprocess timeouts from default 60s to **300s+** to prevent proactor pipe cancellation during heavy AST traversals or test runs.

### Source References
- `src/harness/services/compute_assessor.py`
- `tests/test_compute_assessor.py`
- `AGENTS.md#L27`

### Rule Reference
Governed by AGENTS.md Rule 25.
