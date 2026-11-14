# Monolith Subpackage Decomposition (Axis 2 Remediation)

## Decomposed Modules (<= 250 LOC per file after formatting)
- `src/harness/commands/reflection/`: `group.py`, `runner.py`, `vault_cmds.py`, `export_cmds.py`, `lifecycle_cmds.py`, `lineage_cmds.py`, `graph_cmds.py`, `hygiene_cmds.py`, `timeline_cmds.py`, `__init__.py`.
- `src/harness/services/harness_spawner/`: `constants.py`, `models.py`, `protocols.py`, `helpers.py`, `lifecycle_mixin.py`, `tracking_mixin.py`, `merge_mixin.py`, `persistence_mixin.py`, `engine.py`, `__init__.py`.
- `src/harness/services/dock/`: `models.py`, `safety.py`, `manifest.py`, `protocols.py`, `store.py`, `execution_mixin.py`, `service.py`, `__init__.py`.
