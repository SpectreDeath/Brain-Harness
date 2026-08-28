# CARD: python-dataclass-architect

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SKILL: python-dataclass-architect                                           │
│ CATEGORY: Python Architecture & Performance                                │
│ INVOCATION: /python-dataclass-architect                                     │
│ TRIGGERS: "python dataclass", "dataclass slots", "frozen dataclass",        │
│           "dataclass validation", "derived fields", "optimize python memory"│
│ TARGET: Memory-Efficient, Type-Safe Python @dataclass Modeling              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5-Stage Progression Matrix

| Stage | Focus Area | Primary Technique / Construct | Passing Completion Gate |
| :--- | :--- | :--- | :--- |
| **1. Immutability** | Value Objects vs Entities | `@dataclass(frozen=True)` | Immutability profile decided; automatic hash generation enabled. |
| **2. Memory Profiling** | Descriptor Slotting | `@dataclass(slots=True)` | Per-instance `__dict__` overhead eliminated (~75% byte reduction). |
| **3. Container Isolation**| Default Reference Safety | `field(default_factory=list)` | Mutable containers isolated with factory instantiation. |
| **4. Invariant Validation**| Domain Rules & Derived State| `__post_init__()` + `field(init=False)` | Construction validation asserted; computed fields derived safely. |
| **5. Hierarchy Integrity**| Inheritance & Serialization | Uniform `slots=True` across chain | Inheritance tree slot-safe; `repr/compare` tuned for private state. |

---

## The Three Core Pillars

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SLOTTED MEMORY EFFICIENCY                                │
│ - Eliminates __dict__ allocation per instance.              │
│ - Reduces baseline object size from ~296 bytes to ~72 bytes.│
├─────────────────────────────────────────────────────────────┤
│ 2. VALUE OBJECT IMMUTABILITY                                │
│ - frozen=True prevents post-init attribute assignment.      │
│ - Automatically implements deterministic __hash__() logic.   │
├─────────────────────────────────────────────────────────────┤
│ 3. ENCAPSULATED DERIVED FIELDS                              │
│ - field(init=False) removes derived values from __init__(). │
│ - Derived values calculated in __post_init__ via invariants.│
└─────────────────────────────────────────────────────────────┘
```

---

## Anti-Pattern Invariants Checklist

- [ ] **No Mutable Literals in Defaults**: No `items: list = []` or `meta: dict = {}`; always use `default_factory`.
- [ ] **Uniform Slotted Inheritance**: Every class in the inheritance chain must declare `slots=True`.
- [ ] **Derived Fields Isolated**: Computed variables use `field(init=False)` and are set in `__post_init__`.
- [ ] **Frozen Post-Init Handling**: `object.__setattr__(self, key, val)` used when mutating inside frozen `__post_init__`.
- [ ] **Private State Excluded**: Internal caches and audit tags use `repr=False, compare=False`.
