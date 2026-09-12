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

Entrypoint module and HarnessPlugin implementation for Skill Knowledge Graph & Registry.

#### Classes

- `class SkillGraphPlugin`
  In-process Harness plugin providing SkillGraphService and SkillRegistryService.
  - `def __init__() -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def index(root_dir) -> int`
  - `def find_chain(start_skill, target_skill) -> list[str]`
  - `def query_router(intent, top_k) -> dict[str, Any]`
  - `def export_html_brief(output_path) -> str`
  - `def discover_all(root_dir) -> list[SkillCardDefinition]`
  - `def get_skill(name) -> SkillCardDefinition | None`
  - `def route_intent(intent, top_k) -> dict[str, Any]`
  - `def get_chain(start_skill, target_skill) -> SkillChainResult`
  - `def link_knowledge_vault(vault_dir) -> int`


#### Functions

- `def index_skill_catalog(root_path) -> dict[str, Any]`
  - Scan workspace (.agents/skills, plugins) and construct the knowledge graph.
- `def query_skill_router(intent, top_k) -> dict[str, Any]`
  - Route natural language task intent to matching skills and recommended chains.
- `def find_skill_chain(start_skill, target_skill) -> dict[str, Any]`
  - Find shortest directed execution chain between two skills.
- `def get_skill_topology(skill_name) -> dict[str, Any]`
  - Retrieve full topological inspection for a specific skill.
- `def export_skill_graph_visual(output_path) -> dict[str, Any]`
  - Generate an interactive HTML visual brief in %TEMP%.


### Module [`models.py`](models.py)

Pydantic data schemas for the Skill Knowledge Graph plugin.

#### Classes

- `class EdgeType`
  Semantic relationship types between skills and graph entities.
- `class StageNode`
  A discrete execution stage within a skill.
- `class AntiPatternNode`
  A named failure mode guarded against by a skill.
- `class InvariantNode`
  A non-negotiable architectural invariant or quality checklist item.
- `class SkillNode`
  Core skill node representing an agent capability.
- `class SkillEdge`
  Directed relation between two nodes in the skill knowledge graph.
- `class SkillTopologyReport`
  Topological inspection report for a single skill.
- `class SkillMatch`
  Ranked skill match from the semantic router.
- `class SkillRouterResult`
  Result from query_skill_router.
- `class SkillGraphSnapshot`
  Full snapshot of the skill knowledge graph.


### Module [`parser.py`](parser.py)

Markdown AST and card parser for agent skill files.

#### Classes

- `class SkillCardParser`
  Parses CARD.md and SKILL.md files into structured SkillNode schemas.
  - `def parse_directory(cls, dir_path) -> SkillNode | None`
  - `def scan_root(cls, root_path) -> dict[str, SkillNode]`


### Module [`visualizer.py`](visualizer.py)

Interactive HTML Visual Brief generator for the Skill Knowledge Graph.

#### Classes

- `class SkillGraphVisualizer`
  Renders interactive HTML reports visualizing the agent skill network.
  - `def render_html(cls, graph, output_path) -> str`



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
