"""Domain-partitioned service exports: _agent_orchestration."""
from __future__ import annotations

from harness.services.agent_graph import (
    AGENT_GRAPH_STORE_KEY,
    AgentExecutionGraphService,
    DefaultAgentExecutionGraphService,
    ExecutionGraphEdge,
    ExecutionGraphExport,
    ExecutionGraphNode,
    ThreadSpawnStatus,
)

from harness.services.agent_harness import (
    AGENT_HARNESS_ARCHITECT_SERVICE_KEY,
    AgentHarnessArchitectService,
    ArchitecturalBetRecommendationData,
    FivePartHarnessAuditData,
    FourLayerStackAuditData,
    FourMechanismReliabilityGateData,
    HarnessAuditReportData,
    HarnessComponentStatusData,
    MechanismReliabilityScoreData,
)

from harness.services.ai_native_harness import (
    AI_NATIVE_HARNESS_SERVICE_KEY,
    AiNativeHarnessAuditReportData,
    AiNativeHarnessService,
    BehavioralGateResultData,
    DocDriftItemData,
    FourGatesEvaluationData,
    HarnessDocDriftReportData,
    McpSecurityCheckData,
    NegativeBacklogReportData,
    NegativeQueryDemandItemData,
    PartialPayloadOmissionAuditData,
)

from harness.services.cellcog import (
    CELLCOG_SERVICE_KEY,
    CellCogArtifact,
    CellCogCapabilitiesResult,
    CellCogCapabilityItem,
    CellCogResearchResult,
    CellCogRunResult,
    CellCogService,
    MultimodalCompilationResult,
    MultimodalProtocolCompiler,
)

from harness.services.claude_code import (
    CLAUDE_CODE_BRIDGE_KEY,
    BashGuardrailResult,
    ClaudeCodeBridgeService,
    PromptCompactionResult,
)

from harness.services.coding_harness_calibrator import (
    CODING_HARNESS_CALIBRATOR_SERVICE_KEY,
    BudgetConfigData,
    CalibrationRecommendationData,
    CodingHarnessCalibratorService,
    ContextStagingEventData,
    ContextStagingSimulationData,
    HarnessCalibrationReportData,
    RepatchPredictionData,
    StuckDetectionResultData,
)

from harness.services.context_optimizer import (
    AGENT_CONTEXT_OPTIMIZER_KEY,
    CONTEXT_OPTIMIZER_SERVICE_KEY,
    CompositeContextStrategy,
    ContextOptimizationConfig,
    ContextOptimizationResult,
    ContextOptimizerService,
    ContextPruningStrategy,
    DefaultContextOptimizerService,
    DeterministicPromptPruner,
    MiddleOutObservationCompactor,
    ObservationCompactorStrategy,
    PrunableMessage,
    PruningAuditReport,
    PruningMetric,
    RepoMapInjectionStrategy,
    SlidingWindowPruner,
    estimate_tokens,
    resolve_context_optimizer,
)

from harness.services.openclaw_bridge import (
    OPENCLAW_A2A_KEY,
    OPENCLAW_GATEWAY_KEY,
    OPENCLAW_TOOL_REPAIR_KEY,
    OpenClawA2AService,
    OpenClawA2ATask,
    OpenClawApprovalRequest,
    OpenClawGatewayService,
    OpenClawGatewaySession,
    OpenClawToolBlock,
    OpenClawToolRepairService,
)

from harness.services.openhands_bridge import (
    OPENHANDS_BRIDGE_KEY,
    OpenHandsAction,
    OpenHandsBridgeService,
    OpenHandsEventStream,
    OpenHandsObservation,
)

from harness.services.self_evaluating_pipeline import (
    SELF_EVALUATING_PIPELINE_SERVICE_KEY,
    AgreementReportData,
    DriftAuditData,
    JudgeConsensusData,
    Layer1ReportData,
    RegressionReportData,
    SelfEvaluatingPipelineService,
    StatisticalGateData,
)

from harness.services.webwright_harness import (
    WEBWRIGHT_HARNESS_KEY,
    WebwrightHarnessService,
)

from harness.services.dynamic_model_router import (
    DYNAMIC_MODEL_ROUTER_SERVICE_KEY,
    ComplexityProfileData,
    DynamicModelRouterService,
    ModelConfigData,
    NormalizedResponseData,
    RoutingResolutionData,
)

from harness.services.harness_compass import (
    HARNESS_COMPASS_SERVICE_KEY,
    EvolutionRoundData,
    FeedbackItemData,
    GateResultData,
    GateViolationData,
    GroundedEvidenceData,
    HarnessCompassService,
    HarnessEditData,
    IntegrationManifestData,
)

from harness.services.orca_bridge import (
    ORCA_BRIDGE_KEY,
    OrcaBridgeService,
    OrcaDeliveryBatch,
    OrcaMailboxMessage,
    OrcaMessageConfig,
    OrcaRunConfig,
    OrcaRunInfo,
    OrcaTaskSettlement,
    OrcaWorkerConfig,
    OrcaWorkerDispatchReceipt,
    OrcaWorktreeConfig,
    OrcaWorktreeInfo,
)

from harness.services.uncertainty_guard import (
    UNCERTAINTY_GUARD_SERVICE_KEY,
    BoundaryReportData,
    DocDebtClusterData,
    EscalationTicketData,
    LogprobReportData,
    PipelineReportData,
    RetrievalReportData,
    ScoredChunkData,
    UncertaintyGuardService,
)

from harness.services.context_course import (
    CONTEXT_COURSE_SERVICE_KEY,
    ContextAuditReport,
    ContextCourseService,
    NanoHarnessRunResult,
    SnippetLintResult,
    SwarmDispatchResult,
)

from harness.services.tau_bridge import (
    BranchPath,
    DefaultTauHarnessBridgeService,
    HistoryRepairReport,
    HistoryRepairResult,
    JournalEntryRecord,
    PiHarnessEngine,
    ProjectTrustEvaluation,
    ProjectTrustEvaluator,
    RpcProtocolEnvelope,
    SessionJournalManager,
    SessionNode,
    SessionPathResult,
    SessionTreeResolver,
    TAU_BRIDGE_SERVICE_KEY,
    TAU_HARNESS_BRIDGE_SERVICE_KEY,
    TauBridgeService,
    ToolCallRecord,
    ToolHistoryRepairEngine,
    TrustScope,
    resolve_tau_bridge,
)

from harness.services.opencode_bridge import (
    BUILTIN_OPENCODE_TOOLS,
    DefaultOpenCodeBridgeService,
    OPENCODE_BRIDGE_KEY,
    OpenCodeBridgeService,
    OpenCodeCatalogResult,
    OpenCodeRunResult,
    OpenCodeSessionResult,
    OpenCodeStatusResult,
    resolve_opencode_bridge,
)

