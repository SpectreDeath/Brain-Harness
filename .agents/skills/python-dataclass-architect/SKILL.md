---
name: python-dataclass-architect
description: Design high-performance, memory-efficient, type-safe Python data structures utilizing slots=True, frozen=True, __post_init__ invariant validation, derived fields, and slotted inheritance. Trigger when defining Python entity models, optimizing memory in ETL/data pipelines, enforcing immutable value objects, or constructing complex dataclass hierarchies.
---

# Python Dataclass Architect

`python-dataclass-architect` is the structural design and memory optimization engine for Python `@dataclass` entity models. It eliminates boilerplate, enforces object immutability, reduces memory overhead by ~75% via `slots=True`, validates domain invariants in `__post_init__`, isolates derived fields, and guarantees slot integrity across inheritance hierarchies.

Every dataclass architecture session executes this five-stage progression:

```
[1. Immutability & Hashability Assessment] → [2. Memory Footprint Profiling & Slotting] → [3. Container Isolation & Default Factories] → [4. Invariant Validation & Derived Fields] → [5. Hierarchy Integrity & Representation Tuning]
```

See [CARD.md](CARD.md) for the companion summary card, memory benchmarks, and verification invariants.
Consult `/codebase-design` for deep module design principles and `/data-topology-mapper` for state topologies.

---

## 1. Immutability & Hashability Assessment

Determine whether the data structure represents an immutable Value Object or a mutable Entity:

1. **Value Objects (Immutable)**:
   - Apply `@dataclass(frozen=True)` when the object represents a discrete value that must not change after construction (e.g. coordinates, route segments, configuration snapshots).
   - *Mechanics*: Generates immutable `__setattr__` and `__delattr__` methods that raise `FrozenInstanceError` upon modification attempts.
   - *Automatic Hashability*: Frozen dataclasses automatically generate a compatible `__hash__()` based on equality fields, allowing them to serve as dictionary keys and set members.
2. **Entities (Mutable)**:
   - Use standard dataclasses only when state mutations during object lifecycle are explicitly required by domain logic.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class RouteSegment:
    from_hub: str
    to_hub: str
    distance_km: float
    carrier: str
```

> **Completion criterion**: Mutability profile explicitly decided, with `frozen=True` and automatic `__hash__()` applied to all Value Objects.

---

## 2. Memory Footprint Profiling & Slotting

Eliminate per-instance dictionary overhead in data processing and high-volume systems:

```
┌─────────────────────────────────────────────────────────────┐
│              PYTHON OBJECT MEMORY ALLOCATION                │
├──────────────────────────────┬──────────────────────────────┤
│ Standard Dataclass           │ Slotted Dataclass            │
│ - Uses instance __dict__     │ - Uses __slots__ descriptor  │
│ - ~296 bytes overhead        │ - ~72 bytes overhead         │
│ - Dynamic attribute adding   │ - Fixed, fast attribute slots│
└──────────────────────────────┴──────────────────────────────┘
```

1. **Enable Slot Optimization**:
   - Apply `@dataclass(slots=True)` (Python ≥ 3.10) for high-volume classes, ETL pipelines, or large collections in memory.
2. **Quantify Memory Savings**:
   - Standard instance: `sys.getsizeof(instance.__dict__)` overhead (~296 bytes per object before data).
   - Slotted instance: ~72 bytes total object descriptor footprint, saving ~75% overhead per object.
3. **Combination**:
   - Combine with immutability when optimal: `@dataclass(slots=True, frozen=True)`.

> **Completion criterion**: `slots=True` declared on high-volume and domain entity models, eliminating `__dict__` overhead.

---

## 3. Container Isolation & Default Factories

Prevent the classic shared mutable default argument vulnerability:

1. **Mandatory `default_factory` for Mutable Containers**:
   - Never assign mutable literals (`list`, `dict`, `set`) directly as default values: `items: list[str] = []` (forbidden).
   - Always use `field(default_factory=list)` or `field(default_factory=dict)` to guarantee that every instance receives its own isolated collection.
2. **Dynamic Value Initialization**:
   - For timestamps, UUIDs, or dynamic defaults, use `field(default_factory=datetime.utcnow)` or `field(default_factory=uuid.uuid4)`.

```python
from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass(slots=True)
class OrderBatch:
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    items: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
```

> **Completion criterion**: All mutable containers and dynamic defaults encapsulated via `default_factory`, preventing cross-instance reference sharing.

---

## 4. Invariant Validation & Derived Fields

Enforce structural correctness at construction time and encapsulate calculated state:

1. **Encapsulate Derived Fields with `init=False`**:
   - When a field is computed from other inputs, declare `field(init=False)` to prevent callers from supplying erroneous manual values.
2. **Execute `__post_init__` Assertions**:
   - Validate numerical bounds, string formats, and business constraints inside `__post_init__()`.
   - Raise explicit `ValueError` or `TypeError` on invalid states.
   - Compute and assign the derived fields.
3. **Handling `frozen=True` in `__post_init__`**:
   - If computing derived fields on a frozen dataclass, use `object.__setattr__(self, 'derived_field', computed_value)`.

```python
@dataclass(slots=True)
class Shipment:
    tracking_id: str
    weight_kg: float
    priority: str = "standard"
    freight_cost: float = field(init=False)

    def __post_init__(self) -> None:
        if self.weight_kg <= 0:
            raise ValueError(f"weight_kg must be positive, got {self.weight_kg}")
        rates = {"standard": 1.85, "express": 3.40}
        if self.priority not in rates:
            raise ValueError(f"Invalid priority: {self.priority!r}")
        self.freight_cost = round(self.weight_kg * rates[self.priority], 2)
```

> **Completion criterion**: `__post_init__` validation enforced; derived state isolated with `field(init=False)` and calculated automatically.

---

## 5. Hierarchy Integrity & Representation Tuning

Ensure safe inheritance and tune object serialization and representation:

1. **Enforce Slotted Inheritance Chain**:
   - In Python, if a subclass uses `slots=True`, all parent classes up the inheritance tree must also use `slots=True` (or explicitly define `__slots__`). Mixing slotted and non-slotted classes breaks memory optimization or throws attribute errors.
2. **Exclude Private State from Repr and Equality**:
   - Use `field(repr=False, compare=False)` for internal caches, lock instances, or private audit tags (`_audit_tag`).
3. **Ecosystem Deserialization Bridges**:
   - Use `dacite.from_dict()` for nested dictionary-to-dataclass hydration without manual parsing.
   - Use `marshmallow-dataclass` for automatic schema generation.
   - Upgrade to `pydantic.dataclasses.dataclass` when external JSON API payload validation is required.

> **Completion criterion**: Inheritance chains uniformly slotted; internal fields hidden from `repr` and `compare`; serialization bridge verified.

---

## In-File Reference: Production-Grade Dataclass Template

```python
from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass(slots=True, frozen=True)
class TransactionRecord:
    account_id: str
    amount_cents: int
    currency: str = "USD"
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: list[str] = field(default_factory=list)
    fee_cents: int = field(init=False)
    _audit_hash: str = field(default="", repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.amount_cents <= 0:
            raise ValueError(f"amount_cents must be positive, got {self.amount_cents}")
        fee = int(self.amount_cents * 0.02)
        object.__setattr__(self, "fee_cents", fee)
        object.__setattr__(self, "_audit_hash", f"{self.transaction_id}:{fee}")
```

---

## Anti-Patterns

- **Mutable Default Values** — Setting `items: list = []` directly, leading to shared state across all instances of the class.
- **Unslotted High-Volume Entities** — Creating millions of dataclass instances without `slots=True`, wasting hundreds of megabytes in `__dict__` overhead.
- **Slotted-Unslotted Hierarchy Collision** — Inheriting a `slots=True` class from an unslotted base class, leading to subtle `__dict__` reappearance or attribute crashes.
- **Caller-Exposed Derived Fields** — Leaving computed fields in the `__init__` signature instead of declaring `field(init=False)`, allowing callers to pass conflicting derived values.
- **Post-Init Frozen Mutation without Object Setattr** — Attempting direct assignment `self.cost = x` inside `__post_init__` on a `frozen=True` dataclass, raising `FrozenInstanceError`.
