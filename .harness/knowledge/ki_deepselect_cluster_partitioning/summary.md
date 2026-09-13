# Threadblock Cluster Multi-SM Sequence Partitioning for Wave-Quantization Resilience

## Context
Extracted during automated repository triad ingestion from [`DeepSelect`](D:\GitHub\cloned\Google\DeepSelect) (DeepSeek Sparse Attention TopK kernel).

## Distilled Learning
For workloads with small batch sizes or where total CTAs do not evenly divide the number of active SMs on high-end GPUs, wave quantization leads to severe tail SM idle cycles. DeepSelect groups CTAs into Threadblock Clusters (cluster_size up to 16), divides each sequence into segments across cluster CTAs, and streams local top-k candidates directly into CTA0 in shared cluster memory for final reduction.

## Mental Models
- **Cluster-Level Distributed Reduction**:  Splitting a single batch row across a Threadblock Cluster scales hardware occupancy without increasing overall problem batch size.
- **Distributed Shared Memory (DSMEM)**:  Modern GPU cluster architectures allow CTA0 to read candidate buffers directly from peer CTAs within the cluster with single-cycle locality.

## Decision Heuristics
- Enable cluster variants (cluster_size = 8 or 16) when batch_size is small (< active_SMs / 2) or vocab_size is very large (> 128k).
- For large batch sizes (> total_SMs * 2), disable clusters (cluster_size = 1) to eliminate inter-CTA synchronization overhead.

## Anti-Pattern Defenses
- **Single-CTA Sequence Confinement**:  Forcing one threadblock to process an entire massive sequence alone when GPU SMs sit completely idle in the final wave.
- **Global Memory Staging**:  Writing intermediate CTA top-k reductions back to high-latency HBM global memory instead of utilizing Threadblock Cluster distributed shared memory.

## Triggers & Seam Choices
- **Trigger**: High-throughput TopK kernel design, DeepSeek sparse attention inference, vocabulary sampling, or GPU ALU contention optimization.
- **Seam Choice**: Integration via Brain Harness IoC `ServiceContext` and typed `ServiceKey[DeepSelectTopkProtocol]`.
