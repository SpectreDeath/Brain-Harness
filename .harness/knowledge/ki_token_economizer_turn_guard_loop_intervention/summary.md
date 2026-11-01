# 3-Tier Failure-Loop Intervention & Conjunction Gating

## Context & Theoretical Grounding
When coding agents get stuck, they frequently enter repetitive cycles: re-running failing tests with trivial whitespace edits, ping-ponging between two broken implementations, or repeatedly calling tools with identical failing parameters.

## Distilled Mental Models & Heuristics
1. **3-Tier Cascade Architecture**:
   - **Tier 0 (Free Gate)**: Only inspect trajectory if `turns >= 18` and `error_outputs >= 8`. Evaluated with zero token overhead.
   - **Tier 1 (Strict Heuristic Conjunction)**: Requires a strict conjunction:
     - `edit_churn >= 4` (edits to one file) OR `distinct_edit_files >= 3`
     - AND sustained errors (`error_outputs >= 6`)
     - AND stagnation (`stagnation >= 0.20`, where >=20% of failures repeat an earlier error)
     - AND turn length exceeds repository envelope ($1.25\times$ p90 of resolved tasks).
   - **Tier 2 (Paid LLM Judge)**: Invoked only when the gate is open and heuristics indicate ambiguity. LLM judge must have $\ge 0.70$ confidence.
2. **Hard Backstop Invariant ($2.5\times$)**:
   - If a turn exceeds $2.5\times$ the repository resolved-task envelope, it aborts regardless of judge verdict to prevent catastrophic token drain.
3. **Non-Destructive Mirroring Nudge**:
   - The first intervention is never an abort; it sends a redirect mirroring the agent's recent repetitive actions back at it without external bias.

## Anti-Pattern Defenses
- **Premature Halting**: Aborting productive-but-difficult tasks where error signatures are changing and progress is being made.
- **Unchecked Loop Spirals**: Permitting unbounded model turns where the same error is logged 10+ times.
