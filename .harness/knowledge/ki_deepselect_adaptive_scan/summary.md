# Adaptive Randomized Block Scan with Monotonic Threshold Filtering

## Context
Extracted during automated repository triad ingestion from [`DeepSelect`](D:\GitHub\cloned\Google\DeepSelect) (DeepSeek Sparse Attention TopK kernel).

## Distilled Learning
DeepSelect decouples TopK compaction complexity from vocabulary length N by processing contiguous blocks B in uniform random permutation order, maintaining a monotonic non-decreasing threshold T initialized to -inf. Expected elements processed by in-loop Radix compactions is bounded by E[W] <= (1 + k/B2) * (k + B + B2) * H_m = O(k log(N/k)) when B, B2 = Theta(k).

## Mental Models
- **Random Permutation Decoupling**:  Random block ordering prevents adversarial worst-case inputs and guarantees uniform expectation of high-value element distribution.
- **Monotonic Threshold Shield**:  Once top-k elements are discovered early in the scan, threshold T never decreases, shielding downstream global memory blocks from entering the shared memory compaction buffer.
- **Radix Select in Shared Memory**:  Compaction occurs strictly in-register and shared memory when candidates reach k + B2, eliminating global memory roundtrips.

## Decision Heuristics
- When vocab_size N >> topk k, set block size B and compaction threshold B2 to Theta(k) (typically 1024 for k=512) to minimize total elements processed.
- Always disable sorted_index unless downstream consumption strictly requires sorted order, avoiding unnecessary post-compaction sorting overhead.

## Anti-Pattern Defenses
- **Global Heap TopK**:  Inserting every element of an N-element vector into a min-heap or priority queue causes O(N log k) branch-divergent memory access.
- **Fixed-Stride Scanning**:  Scanning without random block permutation makes the threshold update vulnerable to sorted or clustered adversarial inputs.

## Triggers & Seam Choices
- **Trigger**: High-throughput TopK kernel design, DeepSeek sparse attention inference, vocabulary sampling, or GPU ALU contention optimization.
- **Seam Choice**: Integration via Brain Harness IoC `ServiceContext` and typed `ServiceKey[DeepSelectTopkProtocol]`.
