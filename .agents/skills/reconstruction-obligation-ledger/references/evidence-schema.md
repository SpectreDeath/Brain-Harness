# Canonical Evidence Record Schema Reference

The **Canonical Evidence Record** guarantees content-addressed, immutable traceability for reverse-engineering observations.

## Evidence ID Format

Every evidence record is identified by a deterministic content hash:

```
ev:<sha256(canonical_payload)>
```

The hashing input is serialized using deterministic JSON (keys sorted alphabetically, no insignificant whitespace between tokens, UTF-8 encoding).

## Field Definitions

| Field | Type | Description |
|---|---|---|
| `evidence_id` | `str` | Prefix `ev:` followed by 64-character hexadecimal SHA-256 digest |
| `provider_id` | `str` | Executing tool or provider identity (`ghidra`, `rizin`, `wakaru`, etc.) |
| `subject_format` | `str` | Format of target binary or artifact (`elf`, `pe`, `wasm`, `json`, `dex`) |
| `normalized_result` | `str` | Deterministic canonical JSON serialization of the normalized observation |
| `raw_result` | `str \| None` | Optional raw output or diagnostics emitted by the underlying provider |
| `facet_availability` | `tuple[tuple[str, FacetAvailability]]` | Sorted map of declared facets to availability status |
| `timestamp` | `str` | ISO-8601 UTC timestamp of record creation |

## Facet Availability Semantics

Reverse-engineering tools frequently observe partial surfaces. To prevent false equivalences when comparing functions or surfaces across tools, missing facets must **never** be treated as empty collections.

Each facet must declare an explicit `FacetAvailability` envelope:

```json
{
  "available": false,
  "reason": "Decompiler was unable to resolve indirect jump table"
}
```

- When `available == true`: An empty collection indicates the facet is genuinely empty in the subject artifact.
- When `available == false`: The facet was not observed by the provider; comparisons across this dimension remain `unknown`.
