```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: hf-datasets-engineer                                          │
│ Category: data_engineering                                           │
│ Version: 1.0.0                                                       │
│ Invocation: /hf-datasets-engineer                                    │
│ Triggers: "hf datasets", "datasets engineer", "arrow datasets",      │
│           "lakehouse converter", "streaming dataset"                 │
│ Requires: "data-transformer", "dataset-profiler"                     │
│ Target: High-throughput PyArrow zero-copy tables & streaming streams  │
└──────────────────────────────────────────────────────────────────────┘
```

# Hugging Face Datasets Engineer — Companion Summary Card

## Stage Progression Table

| Stage | Objective | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Manifest & Schema** | Inspect schema, splits, and formats | Schema Metadata | Target dataset schema mapped & split boundaries resolved |
| **Stage 2: Strategy Selection** | Select Arrow mmap vs streaming iterable | Storage Strategy Plan | Storage paradigm chosen & batch budget allocated |
| **Stage 3: Zero-Copy Transforms** | Execute batched lazy mapping and sampling | Stream Sample Report | Sample batch processed & transforms validated |
| **Stage 4: Lakehouse Format** | Serialize to Parquet, Arrow, or JSON | Columnar Dataset File | Dataset serialized with valid columnar metadata |
| **Stage 5: xxhash Verification** | Hash transformation state and record vault | Cache Fingerprint & KI | 100% checks green & transform logged to vault |

---

## Vocabulary & Levers

- **Arrow Zero-Copy**: Accessing memory-mapped binary tabular data buffers directly without deserializing into Python object representations.
- **IterableDataset**: Generator-backed lazy dataset stream evaluated on-demand with minimal memory footprint.
- **Cache Fingerprint**: Deterministic xxhash identifying parent state, transform function bytecode, and execution arguments.
- **Packaged Modules**: Native format readers for 30+ tabular, lakehouse, and biological formats.

---

## Mandatory Invariants Checklist

- [ ] **Eager Materialization Guard**: Never call `list(iterable)` or `to_pandas()` on multi-gigabyte datasets without pagination.
- [ ] **Slotted & Frozen Domain Models**: High-volume entities must declare `slots=True, frozen=True` (Rule 12).
- [ ] **Deterministic Hash Invariance**: Avoid non-deterministic lambdas or closures inside mapping transforms.
- [ ] **Canonical Dual-File Vault**: Knowledge items must be written as directory with `metadata.json` and `summary.md` (Rule 40).
- [ ] **Single-Source Click Seams**: Headless Click commands must be co-located without group shadowing (Rule 6, Rule 10).
- [ ] **Plugin Module Singleton**: Module-level `plugin` singleton must be exported for dynamic discovery (Rule 45).
