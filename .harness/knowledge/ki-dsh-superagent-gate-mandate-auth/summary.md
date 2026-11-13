# DSH Superagent: Two-Layer Deterministic Gate & Mandate Authorization

## Two-Layer Eval
1. **Deterministic Gate (`src/admission.ts#L1-L13`)**: Classifies incoming triggers using `(sender_listed, addressed)` into `explicit`, `inferred`, or `ignore`. Bots can at most produce `inferred` candidates, never `explicit` requests.
2. **Follow-Up Ownership (`docs/002-authorization.md#L18-L45`)**: Human messages on a Ticket's subscribed Thread route directly to that Ticket's Executor without re-entering Eval or expanding its `Mandate` (`strength`, `scope`, `policyVersion`). While owned, the Main Session may only `stop` work; Executors may hand back out-of-scope messages once.
