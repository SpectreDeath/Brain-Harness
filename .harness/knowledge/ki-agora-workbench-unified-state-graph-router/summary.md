# Agora Workbench: Unified Workflow State Graph & Router Disambiguation

## Overview
- **Source Repository**: `https://github.com/microsoft/agora-workbench` (`a8ae030b`)
- **Primary Files**:
  - `src/agora_workbench/code_execution/tools/search/state_graph.py#L160-L371`
  - `src/agora_workbench/connector/models.py#L51-L110`
  - `src/agora_workbench/connector/router.py#L57-L160`

## Core Architecture & Invariants
1. **Explicit Producer/Consumer State Contracts**: Tools declare `state_requires` and `state_produces` tokens (often domain-prefixed such as `powergrid.network_loaded`). When no `states.py` module exists on disk, `_infer_states_from_tools()` synthesizes a domain vocabulary from tool and skill tokens.
2. **Startup-Validated Synthetic Bridge Edges (`inject_bridges`)**: `BridgeEdge(from_state, to_state, description)` links a produced state on Upstream A to a required state on Upstream B as a synthetic `server="(bridge)"` tool transition validated at router startup. Bridges act as workflow planning edges without bypassing runtime auth.
3. **BFS Shortest-Path Workflow Planner (`_find_path`)**: Computes minimum-hop tool + bridge transition chains between `source` and `target`, returning `[]` on identity transitions and `None` when unreachable.
4. **Skill Collision Guard (`_register_unified_load_skill`)**: Maps every upstream skill name; if duplicates span multiple upstreams, requests omitting `upstream` receive an explicit disambiguation error listing colliding upstream names rather than silently shadowing one server.

## Decision Heuristics & Anti-Patterns
- **Never silently overwrite colliding upstream skill names**: Track duplicates explicitly and require caller disambiguation.
- **Never synthesize unvalidated cross-server bridge edges**: Assert `from_state` is produced and `to_state` is consumed before accepting a bridge.
