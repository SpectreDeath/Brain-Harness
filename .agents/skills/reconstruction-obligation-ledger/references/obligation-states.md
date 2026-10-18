# Reconstruction Obligation 8-State Disposition FSM

A **Reconstruction Obligation** formalizes an empirical behavioral expectation extracted from reverse-engineered software surfaces. It advances through an 8-state Finite State Machine (FSM).

## 8-State Taxonomy

1. **`unowned`**: Initial disposition upon behavioral surface registration. Not yet assigned to an implementation file or verified by evidence.
2. **`characterized`**: Grounded by one or more canonical evidence IDs (`ev:<sha256>`). Behavioral inputs, outputs, and constraints are characterized.
3. **`implemented`**: Reconstructed source code exists at a declared `owner_path` with an `owner_sha256` content hash.
4. **`verified`**: Parity tests or package distribution artifacts confirm the reconstructed implementation matches characterized expectations.
5. **`contradicted`**: Contradictory evidence detected (e.g. static disassembler reports procedure X, but live execution trace refutes existence). Quarantines the ledger.
6. **`blocked`**: Upstream technical impediment or missing proprietary dependency prevents reconstruction progress.
7. **`out-of-scope`**: Explicitly documented surface determined to be non-essential or excluded from reconstruction scope with documented rationale.
8. **`unknown`**: Provider retracted observation or dynamic state could not be resolved.

## Valid Transition Graph

| From Disposition | Permitted Target Dispositions | Guard Condition |
|---|---|---|
| `unowned` | `characterized`, `blocked`, `out-of-scope`, `unknown` | `len(evidence_ids) >= 1` for `characterized` |
| `characterized` | `implemented`, `contradicted`, `blocked`, `out-of-scope`, `unknown` | `owner_path != None` for `implemented` |
| `implemented` | `verified`, `contradicted`, `blocked`, `unknown` | Verified by test/distribution artifact |
| `verified` | `contradicted`, `unknown` | Regressed or newly discovered conflict |
| `contradicted` | `characterized`, `blocked`, `out-of-scope`, `unknown` | Re-evaluated with resolving evidence |
| `blocked` | `unowned`, `characterized`, `unknown` | Unblocked |
| `out-of-scope` | `unowned`, `unknown` | Scope reopened |
| `unknown` | `unowned`, `characterized` | Resolved by subsequent observation |

## Cryptographic Closure Guarantee

The ledger is sealed and `is_closed` is claimed **only** when:
- `unowned_count == 0`
- `contradicted_count == 0`
- `total_obligations > 0`
- Canonical SHA-256 closure digest is computed across all sorted obligations.
