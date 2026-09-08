## Deep-Module Monolithic CLI Extraction Pattern

### Pattern
When a skill CLI script exceeds 200 lines of embedded business logic, it must be refactored:
- Extract `XxxEngine` class with `execute_pipeline()` single-pass orchestrator method
- All stage inputs/outputs become slotted/frozen dataclasses (Rule 12)
- CLI becomes a lean adapter < 130 lines that instantiates and delegates to the engine
- No behavioral change; all existing CLI flag signatures preserved as delegation shims (Rule CND-D)

### Two High-Priority Candidates (Sep 8, 2026)

#### context_sync_cli.py → ContextSyncEngine
- Current: 390-line monolith returning raw dicts from clean/sync/lint/audit stages
- Target: `ContextSyncEngine(execute_pipeline())` → `ContextSyncExecutionReport`
- Stage outputs: `AuditResult`, `CleanResult` (frozen), `SyncResult` (frozen), `WorkspaceLintReport`
- Source: architecture-review-context-anti-rot-sync-20260908.html

#### media_pipeline_cli.py → MediaPipelineEngine
- Current: 514-line monolith; 5 stages returning untyped dicts
- Target: `MediaPipelineEngine(execute_pipeline())` → typed `DistilledSeams`, `IsnadLedger`, vault artifacts
- Source: architecture-review-media-to-vault-pipeline-20260908.html

### Canonical Template
```python
@dataclass(slots=True, frozen=True)
class ContextSyncExecutionReport:
    audit: AuditResult
    clean: CleanResult
    sync_result: SyncResult
    lint: WorkspaceLintReport
    duration_ms: float
    success: bool

class ContextSyncEngine:
    def execute_pipeline(self, config: ContextSyncConfig) -> ContextSyncExecutionReport:
        ...  # atomic, importable, testable
```

### Proof Points
- DataManagementEngine: 17 tests in 1.25s (ba193963)
- FileAnalysisEngine: delegation shims zero breakage (0ba8e765)
- developer-docs-architect: 8 tests in 0.21s (35ea24c3)
