# Vercel UI SDK: Git-Diff Framework Expert Routing (expert-scope.mjs) & Multi-Skill Agent Hygiene

**Upstream Repository**: https://github.com/vercel-labs/ui @ `220c1a0d`

## Key Invariants
- **Targeted vs Shared Fan-Out (`scripts/expert-scope.mjs#L17-L95`)**: Changes under `packages/<fw>/`, `apps/docs/content/docs/<docsName>/`, `examples/.../<fw>/`, or `<fw>` playground fixtures trigger only that framework expert (with `web` mapped to `web-components`), while edits in `packages/core/`, `tests/specs/`, or `tests/fixtures.ts` trigger all five (`react`, `vue`, `svelte`, `solid`, `web`).
- **Per-Expert Checkpoint Cursors (`scripts/expert-scope.mjs#L48-L69`)**: Without `--base`, each expert diffs from its own `Last reviewed: <sha>` cursor in `.agents/experts/<fw>/decisions.md`.
- **Internal vs Shipped Skill Separation (`AGENTS.md#L27-L56`)**: Repository-contributing workflows (`ui-sdk-write-code`, `ui-sdk-write-docs`, `ui-sdk-unslop`, `ui-sdk-expert-review`) stay internal under `.agents/skills/`, while end-user component guidance ships inside `@ui-sdk/core` (`packages/core/skills/ui-sdk`).
