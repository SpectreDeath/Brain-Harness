# 5-Level Evidence Validation Playbook

When AI explores an unfamiliar legacy repository, its explanations sound authoritative even when they are incomplete or subtly hallucinated. Every important architectural finding must be validated against the **5-Level Evidence Hierarchy**.

---

## Level 1: Repository Search & AST Introspection
Confirm call sites, references, and usage patterns before assuming code is dead or single-purpose.

* **Find All References**:
  ```bash
  rg "\bcalculate_fee\b" --glob "!tests/*"
  ```
* **Find Call Sites with Arguments**:
  ```bash
  rg "calculate_fee\s*\(" .
  ```
* **Detect Implicit API Contracts (Return Dictionaries)**:
  ```bash
  rg "return\s*\{[^\}]*status" .
  ```

---

## Level 2: Existing Tests & Fixtures
Existing tests reveal boundary assumptions and historical edge cases that source comments do not explain.

* **Search Existing Test Assertions**:
  ```bash
  rg "calculate_fee" tests/
  ```
* **Inspect Test Fixtures**:
  Look for special customer types (e.g. `TIER_3_ENTERPRISE`), negative balances, or magic strings in fixtures.

---

## Level 3: Database Schema & Migration Introspection
Database constraints represent the true ground truth of legacy system assumptions.

* **Audit Nullable Fields and Defaults**:
  Inspect database migration files or SQL DDL for `NOT NULL`, `DEFAULT`, and check constraints.
* **Detect Legacy Column Usages**:
  Verify whether columns with strange names (`cust_legacy_flg_v2`) are still read or written by active queries.

---

## Level 4: Production Observability & Logs
Determine if supposedly obsolete code branches are actively receiving traffic in production.

* **Verify Live Execution**:
  Check application metrics or log streams for log tags emitted inside specific conditional branches before deprecating them.

---

## Level 5: Git Version History & Blame Archaeology
Git commit history explains *why* bizarre code was written when comments are absent.

* **Trace the Exact Commit Introducing a Condition**:
  ```bash
  git log -S "manual_review_required" --all -p
  ```
* **Blame a Specific Line Range**:
  ```bash
  git blame -L 42,55 src/legacy/billing.py
  ```
* **Inspect the Commit Message**:
  Look for issue tickets (e.g. `HOTFIX-8842: prevent negative discount on zero transactions`) explaining legacy workarounds.
