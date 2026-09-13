```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: deepselect-topk-optimizer                                     │
│ Category: data_engineering / deep_learning                           │
│ Version: 1.0.0                                                       │
│ Invocation: /deepselect-topk-optimizer                               │
│ Triggers: "deepselect topk optimizer", "topk dsa selection",         │
│           "sparse attention topk", "denormal fp32 addition"          │
│ Requires: "neural-network-from-scratch", "data-topology-mapper"       │
│ Target: High-throughput TopK kernel design and DSA attention routing │
└──────────────────────────────────────────────────────────────────────┘
```

# DeepSelect TopK Optimizer — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Workload Characterization** | Inspect batch size, vocab length, and topk bounds | Workload Spec | Valid dtype (bf16/fp32), alignment checked |
| **Stage 2: Complexity Bound Estimation** | Calculate harmonic bound and candidate volume | Performance Bound | Expected operations E[W] <= O(k log(N/k)) verified |
| **Stage 3: Hardware Contention Analysis** | Identify ALU vs FP utilization and PTX bitmasking | Hardware Plan | Denormal FP32 bounds and single-pass masks validated |
| **Stage 4: Kernel Dispatch Planning** | Select cluster variant, block sizes B and B2 | Dispatch Plan | Alignment strides (1024-byte row) confirmed |
| **Stage 5: Simulation & Verification** | Execute monotonic threshold filter simulation | Verification Report | 100% top-k selection matches ground truth |

---

## Vocabulary & Levers

- **Monotonic Threshold Shield**: In-shared-memory threshold $T$ that never decreases, exponentially decreasing candidate admission probability.
- **Harmonic Bound ($H_m$)**: The sum of reciprocal block indices bounding expected candidate growth under uniform random block permutation.
- **Denormal FP32 Integer Addition**: Bitwise equivalence of denormal IEEE-754 floats for non-negative integers $\le 2^{22}$.
- **Threadblock Cluster (TMA)**: Grouping CTAs across SMs to process segments of a single sequence in parallel, bypassing tail wave-quantization loss.
- **RadixSelectTopK**: In-shared-memory compaction reducing candidates from $k + B_2$ back to $k$.

---

## Mandatory Invariants Checklist

- [ ] **Strict TopK Ceiling**: Max topk supported is 4096.
- [ ] **Input Alignment Guard**: Row stride must be divisible by 1024 bytes.
- [ ] **Denormal Addition Safety**: Value domain must satisfy 0 <= x, y <= 2^22.
- [ ] **Contiguous Memory Ordering**: Output index buffers must satisfy 32-byte alignment.
