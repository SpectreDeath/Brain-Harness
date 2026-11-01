# Skill Graph & Registry Service

The `harness.services.skill_graph` subpackage orchestrates the skill knowledge graph topology, intent-based skill routing, progressive disclosure cards (`CARD.md`), and topological chain pathfinding across registered agent skills.

---

## Architectural Invariants

- **Typed IoC Registry Key (`Rule 2`, `Rule 35`)**: The skill registry is provided under `SKILL_REGISTRY_SERVICE_KEY` and resolved via `context.require(SKILL_REGISTRY_SERVICE_KEY)`.
- **Strict Graph Reachability (`Rule 55`)**: Chain pathfinding (`get_chain`) returns empty paths and `status: "no_path"` when disconnected, never synthesizing unverified direct edges unless explicitly configured.
- **Router Dictionary Keying (`Rule 35`)**: Intention search matches are keyed strictly by `'skill_name'`.
- **Slotted & Frozen Dataclass Representations (`Rule 12`)**: Skill nodes, links, and route results declare `slots=True` and `frozen=True`.

---

## Module & Symbol Reference

| Module | Core Classes / Symbols | Description |
|---|---|---|
| [`protocols.py`](protocols.py) | `SkillRegistryService`, `SKILL_REGISTRY_SERVICE_KEY` | Protocol defining skill registration, query routing, and DAG chaining contracts. |
| [`models.py`](models.py) | `SkillNode`, `SkillEdge`, `SkillRouteResult`, `SkillChain` | Slotted data models for skill capabilities, frontmatter, and routing paths. |
| [`indexer.py`](indexer.py) | `index_skill_catalog`, `SkillCatalogIndexer` | Filesystem scanner indexing `.agents/skills/` into an in-memory capability graph. |
| [`card_parser.py`](card_parser.py) | `SkillCardParser`, `parse_skill_card` | Parser extracting stage tables and ASCII boxes from `CARD.md` per `Rule 37`. |
| [`routing.py`](routing.py) | `route_intent`, `query_skill_router` | Semantic intent classification and skill recommendation engine. |
| [`topology.py`](topology.py) | `build_skill_dag`, `find_skill_chain` | Topological graph construction and reachability pathfinding. |
| [`scanner.py`](scanner.py) | `scan_skill_directory` | Fast filesystem scanner validating directory structure and metadata. |
| [`intent.py`](intent.py) | `classify_intent` | Intent extraction matching developer prompts to skill capability tags. |
| [`joint_query.py`](joint_query.py) | `execute_joint_query` | Federated multi-criteria skill search combining tags, triggers, and descriptions. |
| [`guidance.py`](guidance.py) | `render_skill_guidance` | Dynamic prompt snippet synthesis for matched skill activations. |
| [`guard/`](guard/) | `StrictGraphReachabilityGuard`, `SkillGraphValidator` | Graph reachability and acyclicity validation guards. |
| [`service/`](service/) | `BuiltinSkillRegistryService` | Core micro-kernel skill registry implementation. |

---

## Usage Recipes

### Querying Skills by Intent
```python
from harness.services.skill_graph.routing import route_intent

def select_skills_for_task(prompt: str):
    result = route_intent(prompt)
    if result.recommended_chain:
        print(f"Recommended workflow: {' -> '.join(result.recommended_chain)}")
    return result.top_skills
```

### Parsing Companion Summary Cards
```python
from pathlib import Path
from harness.services.skill_graph.card_parser import SkillCardParser

parser = SkillCardParser()
card_data = parser.parse_file(Path(".agents/skills/repo-doc-synchronizer/CARD.md"))
print(f"Skill: {card_data.skill_name}, Version: {card_data.version}")
```

