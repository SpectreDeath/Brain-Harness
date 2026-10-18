# Differential Facet Availability Semantics & Multi-Provider Comparison

## Epistemic Lineage & Provenance Snapshot

- **Primary Source Codebase**: `D:\GitHub\cloned\rea-main` (`morluto/rea`)
- **Verified Commit**: `701695139490777ece7a3ccb8508b6215a11c0fe`
- **Source Modules**: `src/domain/comparisonSemantics.ts`, `src/domain/functionComparisonDimensions.ts`, `src/domain/functionComparison.ts`, `src/domain/artifactComparison.ts`, `docs/mcp-contracts.md`

---

## 1. Ground-Truth Mental Models

1. **Facet Availability vs Value Absence**:
   In multi-provider reverse-engineering and security analysis (e.g., comparing Ghidra, IDA Pro, Binary Ninja, and Rizin outputs), a provider may either observe zero occurrences of a feature or fail to inspect that feature entirely. Conflating an unobserved or unsupported facet with an empty set (`count == 0`) corrupts differential analysis. Every observed facet must declare explicit availability:
   `FacetAvailability(available=True)` or `FacetAvailability(available=False, reason="Decompiler does not support CFG emission")`.

2. **The Absence Claimability Gate**:
   Absence is an affirmative negative claim that requires complete traversal proof. An item, symbol, or property can only be legally asserted as absent if and only if the provider's traversal coverage satisfies three predicates:
   `status == "complete"` AND `truncated == False` AND `omitted_count == 0`.
   If coverage is partial, unknown, or truncated, absence claims must be rejected and quarantined as `unresolved`.

3. **3-Valued Differential Outcomes**:
   Traditional binary diffing (`identical` vs `different`) fails in partial-observation environments. Dimensions must resolve to one of three statuses:
   - `unchanged`: Both sides observed the facet with identical normalized content.
   - `changed`: Both sides observed the facet with verifiable divergence.
   - `unknown`: At least one side omitted the facet, declared it unavailable, or failed to declare coverage for an empty collection.
   Overall report status strictly propagates the most conservative verdict: any `unknown` dimension forces the overall status to `unknown`.

4. **Provider Syntax Decoupling**:
   Differing analysis engines use distinct formatting syntaxes (e.g., Intel vs AT&T disassembly, differing decompiler variable naming conventions). Comparing raw string outputs generates false contradictions. Engines must normalize representations to canonical semantics and record representation divergence in `limitations` with conclusion kind `contradiction` rather than semantic mismatch.

---

## 2. Decision Heuristics & Behavioral Rules

- **The Explicit Reason Rule**: Every facet marked unavailable (`available=False`) must declare a non-empty, actionable reason explaining why the provider failed to observe it. Empty or whitespace reasons are rejected by construction invariants.
- **Strict Unknown Propagation**: A differential report cannot conclude `overall_status == "unchanged"` if any dimension outcome is `unknown`. The unknown status must bubble up to preserve audit integrity.
- **Conservative Absence Default**: When coverage is absent or unspecified, an empty facet cannot be assumed complete. Force `status = "unknown"` with null counts and record an undeclared coverage limitation.

---

## 3. Anti-Pattern Defenses

- **Facet Conflation**: Treating an unobserved or undeclared facet as an empty collection (`[]`), producing false zero-deltas in dimension comparison. *Defense*: Hard-fail comparisons unless both sides provide explicit coverage or `available: false`.
- **Undeclared Absence Fallacy**: Asserting that an entity is absent when the provider's traversal coverage was truncated, partial, or `unknown`. *Defense*: Strict boolean gate `absence_claimable = (status == "complete" and not truncated and omitted_count == 0)`.
- **Provider Text False Contradiction**: Equating raw provider formatting (e.g. differing disassembly syntaxes) and asserting functional disparity rather than projecting structural semantics. *Defense*: Isolate syntax divergence into `limitations` with decoupled comparison.
- **Limitation Erasure**: Silently dropping failure and limitation reasons when propagating unresolved dimension outcomes to the summary report. *Defense*: Preserve limitation tuples across dimensions and summary reports.
- **Premature `unchanged` Verdict**: Concluding `unchanged` on the overall report when any dimension carries `unknown` status. *Defense*: Construction assertion enforcing that `overall_status` cannot be `unchanged` if any dimension is `unknown`.

---

## 4. Cross-References & Ecosystem Lineage

- Skill: `differential-facet-verifier` (`.agents/skills/differential-facet-verifier/`)
- Plugin: `plugin.differential_facet_verifier` (`plugins/security_and_forensics/differential_facet_verifier/`)
- Service: `service.differential_facet` (`src/harness/services/differential_facet.py`)
- Related Skills:
  - `reconstruction-obligation-ledger`
  - `adversarial-agent-verifier`
  - `epistemic-isnad-audit`
  - `deep-skill-forge`
