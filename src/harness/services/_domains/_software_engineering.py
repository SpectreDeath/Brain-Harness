"""Domain-partitioned service exports: _software_engineering."""
from __future__ import annotations

from harness.services.doc_builder import (
    DOC_BUILDER_SERVICE_KEY,
    AutodocParameter,
    AutodocSignature,
    AutodocSignatureData,
    DefaultHfDocBuilderService,
    DocBuilderDomainEngine,
    DocChunk,
    DocChunkData,
    DocFormatConvertData,
    DocFormatConvertResult,
    DocLintResult,
    DocLintResultData,
    HfDocBuilderProtocol,
    HfDocBuilderService,
    LinkDiagnostic,
    LinkDiagnosticData,
    LinkValidationReport,
    LinkValidationReportData,
    TocDiagnostic,
    resolve_doc_builder,
)

from harness.services.arch_linter import (
    ARCH_LINTER_KEY,
    ArchLinterService,
    BoundaryCheckResult,
    CircularImportResult,
    DefaultArchLinterService,
    FileDiagnostic,
    FileLintResult,
    ModuleCouplingResult,
    resolve_arch_linter,
)

from harness.services.artifact_generator import (
    ARTIFACT_GENERATOR_KEY,
    ArtifactGeneratorService,
    BriefingResult,
    HtmlReportResult,
    MermaidResult,
)

from harness.services.code_runner import (
    CODE_RUNNER_KEY,
    CodeRunnerService,
    PythonEvalResult,
    PythonExecResult,
    ScriptRunResult,
)

from harness.services.codebase_context import (
    CODEBASE_CONTEXT_SERVICE_KEY,
    CodebaseContextService,
    ConfigResolver,
    ContextGovernanceReport,
    ContextLintReport,
    ContextSmellViolation,
    DefaultCodebaseContextService,
    GovernanceStageResult,
    ManifestScriptInspector,
    PathIntegrityCheck,
    ScriptIntegrityCheck,
    SemanticPathClassifier,
    SyncDriftCheck,
    SyncResult,
    TokenBudgetCheck,
    resolve_codebase_context,
)

from harness.services.doc_synchronizer import (
    DOC_SYNCHRONIZER_SERVICE_KEY,
    BrokenLinkData,
    DocCoverageReportData,
    DocDriftReportData,
    DocSynchronizerService,
    ModuleDocStatusData,
    StaleSymbolData,
)

from harness.services.filesystem_git import (
    FILESYSTEM_GIT_KEY,
    DirListResult,
    FileReadResult,
    FilesystemGitService,
    FileWriteResult,
    GitDiffResult,
    GitLogResult,
    GitStatusResult,
    SearchResult,
)

from harness.services.migration_assistant import (
    MIGRATION_ASSISTANT_KEY,
    MigrationAssistantService,
    PydanticMigrationResult,
    PythonCompatResult,
)

from harness.services.refactor_engine import (
    REFACTOR_ENGINE_KEY,
    CodeTransformResult,
    FunctionExtractResult,
    RefactorEngineService,
    UnusedFunctionsResult,
)

from harness.services.repomap import (
    REPO_MAP_SERVICE_KEY,
    DefaultRepoMapService,
    RepoMapResult,
    RepoMapService,
    SymbolTag,
)

from harness.services.test_runner import (
    TEST_RUNNER_KEY,
    TestDiscoverResult,
    TestRunnerService,
    TestRunResult,
)

from harness.services.pr_lens import (
    PR_LENS_GRAPH_SERVICE_KEY,
    PrLensAnalysisData,
    PrLensCommentData,
    PrLensDiffData,
    PrLensGraphService,
    PrLensRenderData,
    PrLensValidationData,
)

from harness.services.repo_triad_forge import (
    REPO_TRIAD_FORGE_SERVICE_KEY,
    KiCandidateData,
    RepoInspectionData,
    RepoTriadForgeService,
    TriadBriefData,
    TriadPlanData,
    TriadRunData,
)

from harness.services.hyperframes import (
    HYPERFRAMES_SERVICE_KEY,
    DefaultHyperFramesService,
    HyperFramesService,
    RenderOutput,
    RenderRequest,
    VideoScene,
    check_node_available,
    resolve_hyperframes,
)
