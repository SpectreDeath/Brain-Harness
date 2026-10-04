# Dynamic Importlib sys.modules Registration for Slotted/Frozen Dataclasses

## Problem
When writing testing runners or isolated execution bridges that load scripts via `importlib`:
```python
spec = importlib.util.spec_from_file_location("my_module", str(script_path))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```
If `my_module` contains classes decorated with `@dataclass(slots=True, frozen=True)`, Python 3.12 and 3.13 raise:
```
AttributeError: 'NoneType' object has no attribute '__dict__'. Did you mean: '__dir__'?
```
This occurs because `dataclasses._process_class` calls `_is_type` to check for `KW_ONLY` markers:
```python
# CPython dataclasses.py
ns = sys.modules.get(cls.__module__).__dict__
```
Because `module` was never added to `sys.modules`, `sys.modules.get(...)` returns `None`.

## Solution
In all dynamic runners, test fixtures, and sandbox executors, register the module in `sys.modules` before calling `exec_module`:
```python
spec = importlib.util.spec_from_file_location("my_module", str(script_path))
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module  # Non-negotiable invariant for dataclass reflection
spec.loader.exec_module(module)
```

## Provenance
- Python 3.13 standard library `dataclasses.py:757`
- Observed and verified during Stage 5 of `brain-artifact-miner`
- Enforced in `tests/test_brain_artifact_miner.py`
