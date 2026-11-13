# Waza: Canonical SealJSON Admission & Immutable Execution Attempt DAG

**Upstream Repository**: https://github.com/microsoft/waza @ `cc6afc5e`

## Architecture
- **Canonical Digest Sealing (`SealJSON`, `internal/releasepolicy/admission.go#L30-L97`)**: Delete `"digest"` from the JSON object, compute canonical JSON digest over sorted/normalized fields, verify on read alongside strict field presence and `DisallowUnknownFields()`.
- **Release Decision Honesty (`internal/releasepolicy/assess.go#L85-L102`)**: Assesses 7 explicit dimensions (`compatibility`, `completeness`, `assurance`, `golden`, `billing`, `statistics`, `operations`) while emitting explicit non-overclaiming `Limitations` (local hashes do not establish external precommitment; retries do not add independent samples).
- **Attempt DAG & Reuse (`docs/EXECUTION_ATTEMPTS.md#L15-L48`)**: Every submission reserves a 256-bit `exec-<64 hex>` ID; `retry` and `branch` parents form an acyclic DAG capped at 1,024 records; `reuse` verifies reservation, completion, manifest, and artifacts before returning the original terminal unchanged.
