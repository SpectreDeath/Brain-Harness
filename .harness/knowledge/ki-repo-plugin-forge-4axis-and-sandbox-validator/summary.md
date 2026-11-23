# Spawn Learning: plugin_engineering (repo-plugin-forge-1)

- **KI ID**: `ki-repo-plugin-forge-4axis-and-sandbox-validator`
- **Domain**: `plugin_engineering`
- **Status**: `adopted`
- **Source Spawn**: `spawn_harness-repo-plugin-forge_6e908a64` (`repo-plugin-forge-1`)
- **Proposal ID**: `prop_repo-plugin-forge-1_b299226b`

## Transferable Claim
- **Cue**: when ingesting an external GitHub repository to forge a sandboxed Brain Harness plugin
- **Lesson**: run 4-axis deep-repo-auditor inspection first to map entrypoints and hotspots, then scaffold and verify the plugin package with PluginValidator static and dry-run checks before enabling in the IoC container
- **Evidence**: standalone run_audit.py --no-briefs on harness_spawner (files=5, axes=4, composite=0.268) + PluginValidator valid=True (5 checks); stages 01-03 check=pass

## Rationale
Prevents untyped or cyclic foreign code from bypassing ServiceKey contracts or zero-fork config bounds.
