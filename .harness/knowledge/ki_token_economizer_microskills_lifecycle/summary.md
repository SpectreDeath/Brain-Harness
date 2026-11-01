# Experience-Driven Micro-Skills Lifecycle & Asymmetric Contradiction Eviction

## Context & Theoretical Grounding
TokenEconomizer (UC Berkeley & Microsoft Research, arXiv:2610.22732) introduces experience-driven cost control where agents learn repo-specific operational facts across sessions rather than rediscovering them repeatedly.

## Distilled Mental Models & Heuristics
1. **The 3-State Lifecycle**:
   - `CANDIDATE`: Proposed by an environmental fact detector (failing command followed by success) or periodically by an offline distiller review every $k=3$ sessions.
   - `ACTIVE`: Promoted only when confirmed across $K=3$ sessions. For code facts, promotion requires confirmation across distinct edited files (`_drifted_confirms()`) to prevent overfitting to a single file coincidence.
   - `RETIRED`: Facts decay with recency factor $\gamma = 0.8$. Contradictions are penalized asymmetrically with $\lambda = 5.0$. If score drops below 0.0 or a high-stakes fact encounters a single clean contradiction (`HARD_KILL=True`), it is retired immediately.
2. **The Firing Gate**:
   - Even `ACTIVE` facts are only injected into prompt context if their historical firing rate clears $	ext{FIRE\_GATE} \ge 40\%$ over at least 4 exercised sessions. This guarantees prompt budget headroom.

## Anti-Pattern Defenses
- **Speculative Fact Bloat**: Injecting single-session observations without drift verification.
- **Symmetric Forgetting**: Treating failure contradictions with equal weight as confirmations ($\lambda=1.0$), which preserves stale/broken instructions.
