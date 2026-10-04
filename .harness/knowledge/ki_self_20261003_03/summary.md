# Monotonic Threshold Assertions for Dynamic Skill and Plugin Catalogs

## Problem
In an active, expanding agent codebase, skills and plugins are regularly synthesized into `.agents/skills/` and `plugins/`.
Hardcoded assertions in test contracts:
```python
def test_skill_count_parity(self):
    skills = registry.discover_all(".")
    assert len(skills) == 109  # BRITTLE ANTI-PATTERN
```
create an artificial roadblock: every valid new skill immediately causes older unrelated tests to fail with `AssertionError: assert 111 == 109`, creating false-positive build breaks.

## Solution
Author catalog discovery and hygiene tests with monotonic bounds and membership checks:
```python
def test_skill_count_parity(self):
    skills = registry.discover_all(".")
    assert len(skills) >= 109  # Monotonic floor guard
    names = [s.name for s in skills]
    assert "deep-skill-forge" in names
    assert "pi-coding-harness" in names
    assert "brain-artifact-miner" in names

def test_concurrent_scan_double_checked_locking(self):
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = [f.result() for f in futures]
    base_count = len(results[0])
    assert base_count >= 109
    for r in results:
        assert len(r) == base_count  # Thread parity invariant
```

## Provenance
- `tests/test_skill_graph_hardening.py`
- Refactored during `brain-artifact-miner` Stage 5 execution
