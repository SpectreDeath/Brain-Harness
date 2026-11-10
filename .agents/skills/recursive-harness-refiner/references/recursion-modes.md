# Recursion Modes & Topologies

## Parallel Mode (`agg`)

Parallel recursion scales **width**:
1. Base executions: $k$ runs under the unmodified baseline harness.
2. Candidate generation: $2k$ independent proposals ($k$ on the **INV** dimension, $k$ on the **DOM** dimension) evaluated concurrently.
3. Candidate rollouts: Each of the $2k$ candidate harnesses is executed once.
4. Final aggregation: $k$ independent aggregators compose one final harness each (`agg1..aggk`), drawing from all candidate harnesses and rollouts.
5. Final rollouts: Each of the $k$ aggregated harnesses is rolled out once.
6. Total Rollouts: $k$ (base) + $2k$ (candidates) + $k$ (finals) = $4k$.
7. Total Improvement Sessions: $k$ (INV) + $k$ (DOM) + $k$ (compositions) = $3k$.

## Sequential Mode (`seq`)

Sequential recursion scales **depth**:
1. Base executions: $k$ runs under the unmodified baseline harness.
2. For each round $t \in [1, k]$:
   - Propose candidate $INV_t$ and candidate $DOM_t$ based on baseline executions and all prior checkpoints.
   - Roll out $INV_t$ and $DOM_t$ once each.
   - Compose checkpoint $C_t$ from current round candidates and historical checkpoints.
   - Roll out checkpoint $C_t$ once.
3. Final candidate pool: $\{C_1, \dots, C_k\}$.
4. Total Rollouts: $k$ (base) + $2k$ (intermediate candidates) + $k$ (checkpoints) = $4k$.
5. Total Improvement Sessions: $k$ (INV) + $k$ (DOM) + $k$ (compositions) = $3k$.
