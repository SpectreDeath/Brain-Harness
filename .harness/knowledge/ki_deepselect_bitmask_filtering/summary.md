# Single-Pass PTX Bitmask Accumulation & Warp-Level Traversal

## Context
Extracted during automated repository triad ingestion from [`DeepSelect`](D:\GitHub\cloned\Google\DeepSelect) (DeepSeek Sparse Attention TopK kernel).

## Distilled Learning
Traditional filtering requires two scans: one to count qualifying elements for shared memory slot allocation and a second to write them. DeepSelect eliminates the second scan by generating a 32-bit bitmask during the count phase using PTX instructions (set.s32.bf16x2, prmt.b32, dp4a.s32.s32), and subsequent placement traverses candidate indices via hardware __ffs(mask) and bit clearing mask &= mask - 1u.

## Mental Models
- **Bit-Parallel Filtering**:  A single 32-bit register holds the boolean filter decision for up to 32 elements processed by a warp/thread.
- **Sub-register Extraction**:  Instruction-level parallelism via __ffs and mask &= mask - 1u walks only the set bits, achieving O(passing_elements) rather than O(block_size) traversal.

## Decision Heuristics
- In high-throughput GPU filter stages, accumulate boolean predicates into bitmasks in registers rather than writing intermediate booleans to shared memory.
- Utilize hardware find-first-set (__ffs) instructions to directly step across active candidates without evaluating non-qualifying lanes.

## Anti-Pattern Defenses
- **Two-Pass Filter Loop**:  Reading memory or registers twice (pass 1
- **Shared Memory Flag Arrays**:  Storing byte or integer flags in shared memory introduces bank conflicts and wastes valuable cache lines.

## Triggers & Seam Choices
- **Trigger**: High-throughput TopK kernel design, DeepSeek sparse attention inference, vocabulary sampling, or GPU ALU contention optimization.
- **Seam Choice**: Integration via Brain Harness IoC `ServiceContext` and typed `ServiceKey[DeepSelectTopkProtocol]`.
