# Vercel UI SDK: Headless definePrimitive Kernel, Asleep Lazy Wake-Up & Provisional Render Isolation

**Upstream Repository**: https://github.com/vercel-labs/ui @ `220c1a0d`

## Key Invariants
- **Single-Definition Headless Kernel (`packages/core/src/foundation/kernel/primitive.ts#L74-L140`)**: `definePrimitive` unifies initial `state`, non-rendering `live` keys, lazy `asleep` predicates, `controlled` keys (`open`, `value`, `checked` by default), `commits` keys, `api`, `slots`, and `agent` surface hints into a single framework-agnostic definition.
- **Provisional Render Fencing (`packages/core/src/foundation/kernel/primitive.ts#L210-L245`)**: Framework renderers passing `rendering=true` allocate provisional parts without mutating committed props until commit, avoiding side-effect leakage on discarded renders.
- **Asleep Lazy Wake-Up (`packages/core/src/foundation/kernel/primitive.ts#L295-L310`)**: Dormant components (such as closed tooltips or popovers) skip `definition.api(context)` and deferred `bind` calls until `wake()` fires on first interaction or `instance.api` access.
- **Schema Memoization & Live-Key Render Exclusion (`packages/core/src/foundation/kernel/primitive.ts#L499-L524`)**: `schemaOf` caches options/slot schemas per primitive in a `WeakMap`, while `renderVersion` increments only on non-`live` state transitions.
