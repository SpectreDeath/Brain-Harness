# Formal Absence Claimability Rules & Proof Protocol

This reference defines the formal predicates governing negative knowledge claims and entity absence assertions.

## 1. The Core Absence Claimability Predicate

In differential analysis and security auditing, asserting that an entity (e.g. vulnerability, backdoor function, exported symbol, credential string) is **absent** from a binary or codebase requires affirmative proof that the search space was completely evaluated.

An item is legally claimable as absent if and only if:

$$\text{absence\_claimable} \iff (\text{coverage.status} = \text{"complete"}) \land (\neg \text{coverage.truncated}) \land (\text{coverage.omitted\_count} = 0)$$

---

## 2. Truth Table of Absence Validity

| `coverage.status` | `coverage.truncated` | `coverage.omitted_count` | Is Absence Claimable? | Mandatory Result |
|---|---|---|---|---|
| `complete` | `false` | `0` | **YES** | Legally assert absence (`count == 0` is verified) |
| `complete` | `true` | any | **NO** | Reject absence; return `unknown` (truncated traversal) |
| `complete` | `false` | $> 0$ | **NO** | Reject absence; return `unknown` (omitted entries exist) |
| `partial` | any | any | **NO** | Reject absence; return `unknown` (incomplete traversal) |
| `unknown` | any | any | **NO** | Reject absence; return `unknown` (unverified traversal) |
| *missing* | *missing* | *missing* | **NO** | Reject absence; return `unknown` (undeclared coverage) |

---

## 3. Implementation Invariant

Any tool or agent rule attempting to declare an entity absent when `absence_claimable == False` must raise an error or force the dimension status to `unknown` with conclusion kind `unresolved`.
