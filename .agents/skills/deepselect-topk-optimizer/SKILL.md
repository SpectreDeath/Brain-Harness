---
name: deepselect-topk-optimizer
description: Optimize high-throughput TopK selection and DeepSeek Sparse Attention (DSA) workloads using randomized block scans, monotonic threshold filtering, denormal FP32 simulation, and Threadblock Clusters. Do not use for generic sorting or CPU-only arrays.
---

# DeepSelect TopK Optimizer: High-Performance Kernel Architecture & DSA Routing

`deepselect-topk-optimizer` provides domain engineering, performance bound estimation, hardware contention mitigation, and kernel dispatch configuration for high-performance TopK selection kernels derived from the DeepSeek Sparse Attention (DSA) architecture.

See [CARD.md](CARD.md) for the companion summary card, stage progression table, and invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline operational budgets and timeout thresholds.

---

## The 5-Stage TopK Optimization Lifecycle

```
[1. Workload Characterization & Stride Alignment]
                       │
                       ▼
[2. Complexity Bound Estimation & Harmonic Calculus]
                       │
                       ▼
[3. Hardware Contention Mitigation & ALU Planning]
                       │
                       ▼
[4. Kernel Dispatch & Threadblock Cluster Sizing]
                       │
                       ▼
[5. Monotonic Simulation & Verification Protocol]
```

---

## 1. Workload Characterization & Stride Alignment

Analyze input tensor dimensions and hardware alignment requirements:
- **Lightning Indexer Scenario**: `torch.bfloat16`, batch size $1 \sim +\infty$, vocab size $1 \sim +\infty$, small topk ($k \le 4096$). Disable `sorted_index` unless index ordering is mandatory. Set `return_value=False` when values are not consumed (~10% throughput boost).
- **Sampling Scenario**: `torch.float32`, vocab size around 128k, small topk ($k \le 4096$).
- **Stride Invariant**: Row stride of the input tensor must be aligned to `1024` bytes. Output strides must align to `32` bytes.

---

## 2. Complexity Bound Estimation & Harmonic Calculus

Evaluate expected total elements processed across all in-loop TopK calls:
- For input length $N$, block size $B$, and candidate compaction threshold $B_2$, define:
  $$m = \lceil N / B \rceil, \quad L = k + B + B_2, \quad H_m = \sum_{i=1}^m \frac{1}{i}$$
- The expected total elements $W$ processed by RadixSelectTopK across the entire scan satisfies:
  $$\mathbb{E}[W] \le \left(1 + \frac{k}{B_2}\right) L H_m = O\left(k \log\frac{N}{k}\right) \quad \text{when } B, B_2 = \Theta(k)$$
- The compute complexity is completely decoupled from $N$ except logarithmically, ensuring uniform high memory bandwidth utilization.

---

## 3. Hardware Contention Mitigation & ALU Planning

Bypass CUDA Core instruction contention using low-level bit manipulation and IEEE-754 denormal emulation:
- **Single-Pass Bitmask Accumulation**: Use PTX instructions (`set.s32.bf16x2`, `prmt.b32`, `dp4a.s32.s32`) to generate 32-bit boolean masks in registers during count pass. Traverse qualifying elements via hardware `__ffs(mask)` and `mask &= mask - 1u`, eliminating redundant memory passes.
- **Denormal FP32 Simulated Addition**: For non-negative integer operands $x, y \le 2^{22}$, integer addition is bitwise identical to floating-point addition on denormal numbers: `__float_as_uint(__uint_as_float(x) + __uint_as_float(y))`. DeepSelect uses this to bypass integer ALU contention with bitwise/comparison instructions.

---

## 4. Kernel Dispatch & Threadblock Cluster Sizing

Mitigate wave quantization when batch sizes or active SM ratios are low:
- When $\text{batch\_size} < \frac{\text{active\_SMs}}{2}$, enable Threadblock Clusters (`cluster_size = 16`).
- Divide each sequence into segments across CTAs in the cluster; each CTA computes local TopK and streams candidates into CTA0 via distributed shared memory (DSMEM).
- For large batch sizes ($\ge \text{active\_SMs} \times 2$), dispatch non-cluster variants (`cluster_size = 1`) to eliminate inter-CTA synchronization overhead.

---

## 5. Monotonic Simulation & Verification Protocol

Verify selection accuracy and benchmark performance against standard baselines:
- Execute python-level simulation of the randomized block scan, monotonic threshold filter, and shared-memory compaction.
- Assert 100% TopK candidate parity with exact ground truth.
- Verify that input row strides and output buffers adhere strictly to 1024-byte and 32-byte alignment invariants.

---

## The Three Foundational Pillars

### 1. The Decoupled Complexity Bound Pillar
Compaction work must scale as $O(k \log(N/k))$ rather than $O(N \log k)$. By reading global memory strictly once in contiguous blocks and maintaining a monotonic non-decreasing threshold $T$, later blocks rarely pass the filter.

### 2. Hardware ALU Contention Elimination Pillar
Never allow integer addition to bottleneck comparison-heavy kernels. Utilize denormal FP32 addition for values $\le 2^{22}$ and single-pass PTX bitmasks to maximize SM execution pipe concurrency.

### 3. Wave-Quantization Cluster Resilience Pillar
Never allow GPU Streaming Multiprocessors to sit idle during tail execution waves. Partition small-batch sequences across Threadblock Clusters to sustain maximum occupancy.

---

## Anti-Patterns

- **Global Heap Exhaustion** — Inserting all elements of an N-element vector into a global priority queue or heap causing O(N log k) branch-divergent memory access.
- **Two-Pass Filter Stall** — Reading global memory or registers twice for candidate counting and writing, doubling register pressure and stalling pipelines.
- **Integer ALU Saturation** — Using integer multiply-add instructions when int ALU is saturated, delivering half the throughput of floating-point units.
- **Single-CTA Sequence Confinement** — Forcing one threadblock to process an entire massive sequence alone while GPU SMs sit idle in the tail wave.
- **Unbounded Float Denormal Emulation** — Applying denormal FP32 integer addition when operands exceed 2^22, triggering exponent overflow and data corruption.
