# Knowledge Item: Slotted Dataclass Memory & Invariant Architecture

- **ID**: `ki_self_20260828_02`
- **Category**: `performance` / `python_craft`
- **Status**: `VERIFIED`

## Summary & Heuristic

When modeling AST nodes, session traces, or domain entities, standard Python dataclasses allocate an instance `__dict__` and `__weakref__`, consuming ~296 bytes per instance.

### Core Guidelines:
1. **Slotted Dataclasses**: Always specify `@dataclass(slots=True)` on entity models in Python ≥ 3.10 to reduce per-instance footprint to ~72 bytes and accelerate attribute access.
2. **Immutable Value Objects**: Use `@dataclass(slots=True, frozen=True)` for identifier, token, and state snapshot objects, automatically generating deterministic `__hash__()` implementations.
3. **Construction Invariant Validation**: Execute type and invariant validation inside `__post_init__()`:
   ```python
   def __post_init__(self) -> None:
       if self.hop_count < 0:
           raise ValueError(f"hop_count must be non-negative, got {self.hop_count}")
   ```
4. **Mutable Container Defense**: Never use mutable literals (e.g. `items: list = []`) as default values. Always use `field(default_factory=list)`.
5. **Slotted Inheritance**: Ensure all parent classes in an inheritance hierarchy also define `__slots__` or use `slots=True` to maintain the memory optimization across subclasses.
