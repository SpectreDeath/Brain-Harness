# BrainBridge Indexer External & Fixture Pruning (Rule 52)

## Finding (Deep Audit Axis 1)
- `src/harness/services/brain_bridge/indexers.py` pruned VCS and cache directories during `os.walk` but descended into `test_ingested_plugins/` and `plugins/external/`, polluting corpus counts.

## Remediation
- Extended in-place `dirs[:]` pruning to exclude `test_ingested_plugins` and `external`.
- Added regression coverage in `tests/test_brain_bridge_deepened_service.py`.
