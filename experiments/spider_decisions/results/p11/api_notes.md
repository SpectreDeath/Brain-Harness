# Phase 11.1 — `ConsensusEngine.evaluate_cisc_consensus` API Notes

Inspected `src/harness/agent/swarm/consensus.py` (`L250-L361`) and `tests/test_swarm_cisc_integration.py` (`L16-L37`).

## Signature
```python
ConsensusEngine.evaluate_cisc_consensus(
    votes: list[dict[str, Any]],
    *,
    normalization: str = "softmax",
    temperature: float = 2.5,
    only_tie_break: bool = False,
    uncertainty_service: Any | None = None,
) -> dict[str, Any]
```

## Input Vote Shape
Each item in `votes` is a dictionary containing:
- `"choice"`: `str` — candidate answer/design choice identifier.
- `"confidence"`: `float` — scalar trace confidence score (typically `[0.0, 1.0]`).

## Output Dictionary Keys
- `"winner"`: `str` — winning choice string (same value also mirrored in `"decision"`).
- `"confidence"`: `float` — winner's normalized weight fraction (`totals[winner] / sum(totals)`).
- `"weights"`: `dict[str, float]` — total aggregated weight per choice.
- `"consensus_reached"`: `bool` — `True` when a winner is selected.
- `"valid_trace_count"`: `int` — number of valid traces aggregated.
- `"status"`, `"total_votes"`, `"normalization"`, `"is_tie"`, `"source"`: execution metadata (`"builtin_cisc"` without `uncertainty_service`).
