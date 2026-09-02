# Kit Fine Counterfactual Fault Localization & Truthmaker State Fragment Fusion

## Context
When multi-agent workflows or formal invariant checks fail, debugging against the entire context state (hundreds of triples or files) leads to hallucinated explanations. Truthmaker semantics provides hyperintensional grounding by extracting only the minimal sub-state that strictly makes a proposition true or false.

## Distilled Learning
1. **State Fragments & Join Fusion ($s \sqcup t$)**:
   - Represent atomic state subsets as `StateFragment(triples=[...])`.
   - Compute join fusion (`s.fusion(t)`) via set union over verified state triples, eliminating irrelevant context.
2. **Exact Truthmaker Classification ($s \Vdash A$)**:
   - Filter state triples down strictly to `relevant_predicates` associated with proposition $A$.
   - If relevant triples are missing or conflicting, classify as `ExactFalsemaker`.
3. **Counterfactual Fault Localization**:
   - Compare `expected_predicates` against actual triples to identify missing predicates and isolating violating triples into a minimal fault sub-state `minimal_fault_substate`.

## Triggers & Seam Choices
- **Trigger**: Invariant verification failure, epistemic Isnad audit validation, or agent error diagnosis.
- **Seam Choice**: Integrate within `harness.services.epistemic_audit` or `diagnosing-bugs` loops to produce minimal proof trails.
