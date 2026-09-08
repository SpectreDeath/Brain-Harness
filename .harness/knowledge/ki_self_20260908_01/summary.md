## SkillPipelineEngine Unification Invariant

### Problem
All 42 skill execution drivers (orchestrators, forges, pipeline scripts) independently implement:
- Ad-hoc `StageResult` / `Report` dataclasses without slotted/frozen invariants (Rule 12 violation)
- Manual execution timing in each driver
- Isolated Windows UTF-8 stream setup (Rule 23) repeated across files
- No EventBus telemetry hookup
- 400+ LOC of duplicated boilerplate across `.agents/skills/*/scripts/*.py`

### Invariant
All skill execution drivers must inherit from or compose `BaseSkillPipelineEngine` 
defined in `src/harness/services/skill_pipeline.py`. Canonical slotted/frozen value 
objects `SkillStageResult` and `SkillPipelineReport` replace all ad-hoc dict returns.

### Canonical Pattern
```python
from harness.services.skill_pipeline import BaseSkillPipelineEngine, SkillStageResult

class ModernizationOrchestrator(BaseSkillPipelineEngine):
    def execute_pipeline(self, request: ModernizationRequest) -> SkillPipelineReport:
        stages: list[SkillStageResult] = []
        stages.append(self._run_stage("audit", self._audit, request))
        stages.append(self._run_stage("plan", self._plan, request))
        stages.append(self._run_stage("execute", self._execute, request))
        return self._finalize_report(stages)
```

### Benefits
- Automatic stage isolation, timing, and error capture
- Universal EventBus `SkillStageCompletedEvent` publishing
- Removes 400+ LOC from 42 drivers in a single refactor
- Testable without mocking collaborators

### Evidence
- architecture-review-20260908_063207.html: Candidate 1, rated STRONG
- 42 ad-hoc skill scripts in `.agents/skills/*/scripts/`
- Existing shell: `src/harness/services/skill_pipeline.py` (not yet used by drivers)
