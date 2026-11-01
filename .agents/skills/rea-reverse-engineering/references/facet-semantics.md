# Facet Availability Semantics & Absence Claimability

The REA toolkit strictly separates "not observed" from "zero occurrences" through 3-valued facet availability semantics:

## 1. The Three Facet States

1. **`available`**: The facet was actively inspected by an enabled provider and produced one or more verified structural observations.
2. **`absent`**: The provider completed a full, untruncated traversal with zero omitted entities, affirmatively proving that zero instances exist.
3. **`unknown`**: The facet was not declared, the provider was missing/disabled, or traversal was truncated/partial.

## 2. Formal Absence Claimability Gate

An absence assertion (`state: "absent"`) is legally valid **if and only if**:

$$\text{absence\_claimable} \iff (\text{coverage.status} = \text{"complete"}) \land (\neg \text{coverage.truncated}) \land (\text{coverage.omitted\_count} = 0)$$

If any of the following conditions hold, absence claims are strictly rejected:
- Traversal was truncated due to budget caps (`max_symbols`, `max_records`).
- Provider status is `partial` or `unknown`.
- Provider binary is not installed on the host (e.g. headless Ghidra or JADX missing).
- Traversal omitted one or more records (`omitted_count > 0`).

In all such cases, the facet state is quarantined as `unknown` with a non-empty `reason`.

