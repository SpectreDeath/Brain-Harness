# Deep Repo Auditor Plugin (`plugin.deep_repo_auditor`)

Micro-kernel IoC adapter exposing the `DeepRepoAuditorService` (`service.deep_auditor`) to inspect repositories across four structured axes, score 5D compute complexity, classify module/agent topology, and render interactive dark-mode HTML visual briefs.

## Entrypoints

- `deep_audit_repo(repo_path)` — Execute 5D compute assessment, bounded filesystem scan, and 4-axis introspection.
- `deep_audit_briefs(repo_path, output_dir=None)` — Generate the three dark-mode HTML visual briefs (`compute-assessor`, `data-topology-review`, `repo-reader`).
- `deep_audit_ki_candidates(repo_path)` — Extract structured Knowledge Item candidates anchored to audited axes.
- `deep_audit_full(repo_path, output_dir=None)` — Run full end-to-end audit, brief generation, and KI extraction.

## Service Registration

- Registers `DEEP_AUDITOR_SERVICE_KEY` (`service.deep_auditor`) via `on_load(context)` using `DefaultDeepRepoAuditorService` from `harness.services.deep_auditor`.
