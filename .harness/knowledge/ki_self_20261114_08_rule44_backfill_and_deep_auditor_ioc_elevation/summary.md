# Rule 44 Backfill & Deep Repo Auditor Elevation (Axis 4)

## Remediation
- Backfilled `config.default.yaml` across all 11 missing `.agents/skills/` packages and 82 internal `plugins/` directories (excluding external bundles).
- Elevated `/deep-repo-auditor` into `src/harness/services/deep_auditor/` (`DEEP_AUDITOR_SERVICE_KEY`), `plugins/software_engineering/deep_repo_auditor/`, and `.agents/skills/deep-repo-auditor/scripts/run_audit.py` with full contract coverage in `tests/test_service_deep_auditor.py`.
