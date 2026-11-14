# Graphiti: Bi-Temporal Edge Normalization & Contradiction Invalidation

## Overview
- **Source Repository**: `https://github.com/getzep/graphiti` (`ed231965`)
- **Primary Files**:
  - `graphiti_core/utils/maintenance/temporal_edge_utils.py#L14-L96`
  - `graphiti_core/utils/maintenance/edge_operations.py#L250-L380`

## Core Architecture & Invariants
1. **Bi-Temporal Coordinates**: System ingestion lifetime `(created_at, expired_at)` is strictly separated from world-event truth interval `(valid_at, invalid_at)`.
2. **Future-Tense Clamping (`normalize_future_temporal_bounds`)**: When a fact matches `_FUTURE_ASSERTION_RE` (`will`, `plans to`, `scheduled to`, etc.) and `valid_at > reference_time`, `valid_at` is clamped back to `reference_time` because the commitment/plan holds true from statement time onward.
3. **Soft Deadline Filtering**: When `invalid_at > reference_time` accompanies `_DEADLINE_RE` (`by`, `before`, `deadline`, `due by`) without an explicit termination marker in `_ONGOING_STATE_END_RE` (`until`, `expires`, `ceases`), `invalid_at` is cleared (`None`) so target dates do not falsely invalidate active plans.
4. **Contradiction Expiration (`resolve_edge_contradictions`)**: Superseded edges remain auditable with `invalid_at = new_edge.valid_at` and transaction `expired_at = utc_now()`.

## Decision Heuristics & Anti-Patterns
- **Never treat target deadlines in plans as `invalid_at` bounds**: Check `_ONGOING_STATE_END_RE` before persisting `invalid_at`.
- **Never overwrite `valid_at` on future commitments with the event date**: Clamp `valid_at` to `reference_time`.
