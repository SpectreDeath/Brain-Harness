"""Domain-partitioned service exports: _data_engineering."""
from __future__ import annotations

from harness.services.bigquery_augmented_analytics import (
    BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY,
    AugmentedInvestigationData,
    BigQueryAugmentedAnalyticsService,
    CausalEffectData,
    CausalTrajectoryPointData,
    ChangePointItemData,
    ChangePointsData,
    DriverSegmentItemData,
    ExecutiveDiagnosticNarrativeData,
    KeyDriversData,
    SeasonalityCycleData,
    TemporalProfileData,
    TemporalTrendPointData,
)

from harness.services.data_management import (
    DATA_MANAGEMENT_SERVICE_KEY,
    BuiltinDataManagementService,
    DataManagementEngine,
    DataManagementPlugin,
    DataManagementService,
    MedallionPipelineConfig,
    MedallionPipelineResult,
)

from harness.services.gods_eye_view import GODS_EYE_VIEW_SERVICE_KEY, GodsEyeViewService

from harness.services.symbolic_solver import (
    SYMBOLIC_SOLVER_KEY,
    ConstraintSolveResult,
    LogicQueryResult,
    MathEvalResult,
    SymbolicSolverService,
)

from harness.services.deepselect_topk import (
    DEEPSELECT_TOPK_SERVICE_KEY,
    DeepSelectTopkProtocol,
)

from harness.services.deterministic_validation import (
    DETERMINISTIC_VALIDATION_SERVICE_KEY,
    DeterministicValidationService,
    LoopExecutionResultData,
    TriageRecordData,
    ValidationResultData,
)

from harness.services.paperless_ngx import (
    PAPERLESS_NGX_SERVICE_KEY,
    DefaultPaperlessNgxService,
    DocumentSummary,
    GroundedRAGAnswer,
    IngestionReceipt,
    PaperlessConfig,
    PaperlessNgxService,
    RAGAnswer,
    TaskProgress,
)

from harness.services.garf_reporting import (
    GARF_REPORTING_SERVICE_KEY,
    DefaultGarfReportingService,
    GarfExecutionReceipt,
    GarfQuerySpec,
    GarfReportBatch,
    GarfReportingService,
    GarfWorkflowStep,
)

from harness.services.hf_datasets import (
    HF_DATASETS_SERVICE_KEY,
    DefaultHfDatasetsService,
    HfColumnSchema,
    HfDatasetMetadata,
    HfDatasetVaultCommit,
    HfDatasetsService,
    HfStorageStrategy,
    HfStreamConfig,
    HfTransformationSpec,
    HfTransformResult,
)

from harness.services.open_source_gis import (
    CRSProjectionError,
    DefaultOpenSourceGisService,
    EngineSelectionResult,
    FalconViewRestrictedDomainError,
    GISEngineCatalog,
    GISEngineRecord,
    GISEngineScore,
    GisVisualBriefResult,
    OPEN_SOURCE_GIS_SERVICE_KEY,
    OpenSourceGisService,
    SpatialArchitectureReceipt,
    SpatialPipelineDAG,
    SpatialPipelineStep,
    SpatialWorkloadProfile,
    TopologyAuditReport,
    TopologyValidationError,
    resolve_open_source_gis,
)

from harness.services.discovery_index import (
    DISCOVERY_INDEX_SERVICE_KEY,
    DiscoveryIndexService,
    DiscoverySearchResult,
    DiscoverySourceModel,
    DiscoveryStatsModel,
    LocalDiscoveryIndexService,
)

from harness.services.rea_javascript import (
    REA_JAVASCRIPT_KEY,
    DotnetInspectReport,
    ElectronInspectReport,
    HarInspectReport,
    ReaJavaScriptService,
    RecoverSourcesReport,
    WebObservationReport,
    resolve_rea_javascript,
)

from harness.services.differential_facet import (
    DIFFERENTIAL_FACET_SERVICE_KEY,
    FACET_AVAILABILITY_SERVICE_KEY,
    DifferentialFacetService,
    StandardDifferentialFacetService,
    DifferentialFacetAvailability,
    CoverageDeclaration,
    DimensionOutcome,
    DifferentialReport,
    VALID_DIMENSIONS,
    resolve_differential_facet,
)
