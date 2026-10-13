# plugin.skill_knowledge_graph (v1.0.0)

Knowledge graph indexer, semantic router, and visual topology generator for agent skill cards

---

## Overview & Metadata

- **Plugin Directory**: `plugins/memory_and_epistemics/skill_knowledge_graph`
- **Isolation Mode**: `in_process`
- **Services Provided**: `service.skill_knowledge_graph`, `service.skill_registry`
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `index_skill_catalog` | `(root_path)` | Scan workspace (.agents/skills and plugin directories) to build the in-memory skill knowledge graph |
| `query_skill_router` | `(intent, top_k)` | Find the optimal skill or multi-skill execution chain for a given task description or intent |
| `find_skill_chain` | `(start_skill, target_skill)` | Compute the shortest directed path or multi-skill pipeline from a start skill to a target objective |
| `get_skill_topology` | `(skill_name)` | Retrieve upstream prerequisites, downstream handoffs, invariants, and mitigated anti-patterns for a given skill |
| `export_skill_graph_visual` | `(output_path)` | Generate an interactive visual HTML brief in %TEMP% rendering the Mermaid DAG of all skills and category clusters |

---

## Key Modules & AST Symbols

### Module [`graph.py`](graph.py)

Directed Knowledge Graph engine for indexing, routing, and chaining skills.

#### Classes

- `class SkillKnowledgeGraph`
  In-memory directed knowledge graph representing skills, categories, and relationships.
  - `def __init__() -> None`
  - `def add_skill(skill) -> None`
  - `def build_derived_edges() -> None`
  - `def query_router(intent, top_k) -> SkillRouterResult`
  - `def find_chain(start_skill, target_skill) -> list[str]`
  - `def get_topology(skill_name) -> SkillTopologyReport`
  - `def generate_mermaid() -> str`
  - `def get_snapshot() -> SkillGraphSnapshot`


### Module [`main.py`](main.py)

Entrypoint module re-exporting standalone tools and instantiated plugin singleton.
- Single-Seam Resolver: `resolve_skill_knowledge_graph(context)` (Rule 58)
- Plugin Singleton: `plugin = SkillGraphPlugin()` (Rule 45)

### Module [`service.py`](service.py)

`SkillGraphPlugin` implementing `HarnessPlugin`, `ToolMountMixin`, and protocol mixins for graph, registry, clustering, and intelligence services.

### Module [`mixins.py`](mixins.py)

Service protocol mixin implementations:
- `GraphServiceMixin`: `SkillGraphService` methods
- `RegistryServiceMixin`: `SkillRegistryService` methods
- `ClusteringServiceMixin`: `SkillClusteringService` methods
- `IntelligenceServiceMixin`: `SkillIntelligenceService` methods

### Module [`tools.py`](tools.py)

Core workspace indexing, router queries, directed pathfinding, and visual topology exports.

### Module [`clustering_tools.py`](clustering_tools.py)

Skill domain clustering, emergent capability discovery, cross-cluster bridges, and execution guidance compilation.

### Module [`resolvers.py`](resolvers.py)

Single-seam IoC resolver `resolve_skill_knowledge_graph(context)` adhering to Rule 58.


### Module [`models.py`](models.py)

Pydantic data schemas for the Skill Knowledge Graph plugin. Re-exports canonical service models from `harness.services.skill_graph` with backward-compatible aliases while declaring plugin-specific result schemas.

#### Plugin Schemas

- `class SkillMatch`
  Ranked skill match from the semantic router.
- `class SkillRouterResult`
  Result from query_skill_router.
- `class SkillGraphSnapshot`
  Full snapshot of the skill knowledge graph.

#### Canonical Service Re-exports & Aliases

The following types are canonical models defined in `harness.services.skill_graph` and re-exported for backward compatibility:
- `EdgeType`: Semantic relationship types between skills and graph entities.
- `StageNode` (alias for `SkillStageDefinition`): A discrete execution stage within a skill.
- `AntiPatternNode` (alias for `SkillAntiPatternDefinition`): A named failure mode guarded against by a skill.
- `InvariantNode` (alias for `SkillInvariantDefinition`): A non-negotiable architectural invariant or quality checklist item.
- `SkillNode` (alias for `SkillCardDefinition`): Core skill node representing an agent capability.
- `SkillEdge`: Directed relation between two nodes in the skill knowledge graph.
- `SkillTopologyReport`: Topological inspection report for a single skill.


### Module [`parser.py`](parser.py)

Markdown AST and card parser for agent skill files.

#### Architectural Delegation

In accordance with Rule 49 (Skill-to-IoC Micro-Kernel Seam Elevation Invariant), parsing logic is elevated into the core micro-kernel service `harness.services.skill_parser.SkillCardParser`. This module re-exports `SkillCardParser` for backward compatibility:
- `SkillCardParser`: Authoritative parser from `harness.services.skill_parser` providing `parse_directory(cls, dir_path)` and `scan_root(cls, root_path)`.


### Module [`visualizer.py`](visualizer.py)

Interactive HTML Visual Brief generator for the Skill Knowledge Graph.

#### Architectural Delegation

In accordance with Rule 49 (Skill-to-IoC Micro-Kernel Seam Elevation Invariant), rendering logic is elevated into `harness.services.skill_visualizer.SkillGraphVisualizer`. This module re-exports `SkillGraphVisualizer` for backward compatibility:
- `SkillGraphVisualizer`: Authoritative renderer from `harness.services.skill_visualizer` providing `render_html(cls, graph, output_path)`.



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
