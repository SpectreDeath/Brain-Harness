# Phase 10.1 — Standalone Skill Router Construction Recipe

`BuiltinSkillRegistryService` can be constructed and queried directly without initializing the micro-kernel (`ServiceContext` / IoC bootstrap):

```python
from harness.services.skill_graph import BuiltinSkillRegistryService

svc = BuiltinSkillRegistryService()
svc.discover_all(str(WORKSPACE))
result = svc.route_intent(intent, top_k=3)
# result["matches"] contains dicts keyed by "skill_name" (Rule 35), "confidence", "raw_score", "matched_triggers"
# result["recommended_chain"] contains list[str]
```

## Verified Details
- **Source modules:** `src/harness/services/skill_graph/__init__.py` (re-exporting `BuiltinSkillRegistryService` from `harness.services.skill_graph.service`), `src/harness/services/skill_graph/adapter.py` (`SkillIntelligenceAdapter` delegating `.discover_all()` and `.route_intent()`), and `src/harness/services/skill_graph/routing.py` (DAG pathfinding helpers).
- **Smoke check observed:** Calling `svc.discover_all(".")` indexed `total_indexed: 149` skills across the workspace and `svc.route_intent("audit this repository architecture", top_k=3)` returned `'status': 'ok'` with top match `skill_name='deep-repo-auditor'` and `recommended_chain=['deep-repo-auditor']`.
- **Note:** Look up matched skill identifiers using `match.get("skill_name") or match.get("name")` per `AGENTS.md` Rule 35.
