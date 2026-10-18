"""Domain-partitioned service exports: _memory_and_epistemics."""
from __future__ import annotations

from harness.services.brain_bridge import (
    BRAIN_BRIDGE_KEY,
    BrainAttachResult,
    BrainBridgeService,
    BrainDetachResult,
    BrainListResult,
    BrainQueryResult,
    DefaultBrainBridgeService,
    detect_brain_format,
    is_git_url,
    resolve_brain_bridge,
)

from harness.services.context_compactor import (
    CONTEXT_COMPACTOR_KEY,
    CompactConversationResult,
    ContextCompactorService,
    OffloadMemoryResult,
    RecallMemoryResult,
)

from harness.services.context_type_system import (
    CONTEXT_TYPE_SYSTEM_KEY,
    ContextTypeService,
)

from harness.services.embedding_cluster import (
    EMBEDDING_CLUSTER_KEY,
    ClusterKeywordsResult,
    ClusterTextResult,
    EmbeddingClusterService,
)

from harness.services.graphiti import GRAPHITI_MEMORY_KEY, GraphitiService

from harness.services.memgraphrag import MEMGRAPHRAG_MEMORY_KEY, MemGraphRAGService

from harness.services.prompt_benchmark import (
    PROMPT_BENCHMARK_KEY,
    ModelOutputEvalResult,
    PromptBenchmarkService,
    RegressionMatrixResult,
    TextSimilarityResult,
)

from harness.services.semantic_cache import (
    SEMANTIC_CACHE_KEY,
    CacheClearResult,
    CacheEntry,
    CacheGetResult,
    CacheSetResult,
    CacheStatsResult,
    SemanticCacheService,
)

from harness.services.skill_graph import (
    CANONICAL_PIPELINE_PRECEDENCE,
    SKILL_GRAPH_KEY,
    SKILL_INTELLIGENCE_KEY,
    SKILL_REGISTRY_KEY,
    ActionGateResult,
    BuiltinSkillGraphService,
    BuiltinSkillRegistryService,
    SkillCardDefinition,
    SkillChainResult,
    SkillExecutionGuidance,
    SkillGraphService,
    SkillIntelligenceAdapter,
    SkillIntelligenceService,
    SkillInvariantDefinition,
    SkillNode,
    SkillRegistryPlugin,
    SkillRegistryService,
    resolve_skill_intelligence,
)

from harness.services.skill_parser import SkillCardParser

from harness.services.skill_visualizer import SkillGraphVisualizer

from harness.services.unified_context import (
    UNIFIED_CONTEXT_PIPELINE_KEY,
    DefaultUnifiedContextPipeline,
    UnifiedContextPipelineService,
    UnifiedContextRequest,
    UnifiedContextResult,
)

from harness.services.vector_index import (
    VECTOR_INDEX_KEY,
    VectorHybridSearchResult,
    VectorIndexResult,
    VectorIndexService,
    VectorSearchResult,
)

from harness.services.okf_memory import (
    OKF_MEMORY_SERVICE_KEY,
    OKFConceptRecord,
    OKFGovernanceScope,
    OKFMemoryService,
    OKFSearchResult,
    OKFValidationReport,
)

from harness.services.brain_artifact_miner import (
    BRAIN_ARTIFACT_MINER_KEY,
    ArtifactLifecycleEntry,
    BrainArtifactMinerService,
    ByteOffsetEntry,
    DualTranscriptStep,
    ScratchCatalog,
    ScratchCatalogItem,
    StandardBrainArtifactMinerService,
    TaskTriageReport,
    resolve_brain_artifact_miner,
)

from harness.services.conversation_trajectory_miner import (
    CONVERSATION_TRAJECTORY_MINER_KEY,
    ByteOffsetSeekTable,
    CognitiveBifurcationReport,
    ConversationManifest,
    ConversationTrajectoryMinerService,
    FailureCluster,
    FrictionScorecard,
    IsnadClaimRecord,
    StandardConversationTrajectoryMinerService,
    TrajectoryStepRecord,
    resolve_conversation_trajectory_miner,
)

from harness.services.temp_artifact_miner import (
    TEMP_ARTIFACT_MINER_KEY,
    BriefCatalog,
    BriefCatalogItem,
    IsnadAttributionRecord,
    SandboxFixture,
    SandboxReport,
    StandardTempArtifactMinerService,
    TempArtifactMinerService,
    VisualSalvageReport,
    CognitiveBifurcationReport as TempCognitiveBifurcationReport,
    resolve_temp_artifact_miner,
)

from harness.services.skill_clustering import (
    CANONICAL_EMERGENT_PATTERNS,
    SKILL_CLUSTERING_SERVICE_KEY,
    CrossClusterBridge,
    DefaultSkillClusteringService,
    EmergentCapability,
    SkillCluster,
    SkillClusteringEngine,
    SkillClusteringService,
    SkillSelectionPlan,
    generate_clustered_mermaid,
    resolve_skill_clustering,
)

from harness.services.reconstruction_obligation import (
    RECONSTRUCTION_OBLIGATION_SERVICE_KEY,
    CanonicalEvidence,
    FacetAvailability,
    ObligationItem,
    ReconstructionObligationService,
    ReconstructionProof,
    StandardReconstructionObligationService,
    resolve_reconstruction_obligation,
)
