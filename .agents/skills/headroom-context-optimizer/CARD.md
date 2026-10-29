┌────────────────────────────────────────────────────────────────────────┐
│ SKILL: headroom-context-optimizer                                      │
├────────────────────────────────────────────────────────────────────────┤
│ Optimize context budgets, compress tool returns, deduplicate turns,    │
│ and detect prompt cache drift using Headroom context engineering.      │
└────────────────────────────────────────────────────────────────────────┘

## 5-Stage Progression Matrix

| Stage | Operation | Primary Output | Gate Condition |
| --- | --- | --- | --- |
| 1. Trigger | Detect syntax & measure tokens | Format Classification | Exceeds min length threshold |
| 2. ContentRouter | SmartCrush & format compression | Compacted text | Savings ratio $\ge 0.20$ |
| 3. CCR Dedup | Fold repetitive multi-turn returns | Digest markers | Duplicate tool blocks folded |
| 4. Cache Check | Scan system prompt for drift | Volatility Report | Zero volatile tokens or flagged |
| 5. Ledger | Record tokens & dollars saved | SavingsLedger | Cumulative ledger committed |

---

## Mandatory Invariants Checklist

- [ ] All compressed text structures must preserve critical syntax delimiters (valid JSON, valid code).
- [ ] System prompts must remain 100% byte-identical across requests; cache aligner operates in detector-only mode.
- [ ] Dedup markers must only replace runs $\ge 3$ lines and $\ge 40$ characters to guarantee positive net savings.
- [ ] Slotted domain models must use `slots=True, frozen=True` with `__post_init__` construction assertions.
- [ ] Bundled runner scripts must configure standard streams to UTF-8 and execute non-interactively without `input()`.
