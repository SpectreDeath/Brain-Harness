"""Authoritative Skill Knowledge Graph & Registry package (decomposed).

Exposes typed models, protocols, indexing, AST guard, routing, scanning, topology,
intent routing, execution guidance, and registry services.
Preserves 100% backward compatibility for all module-level imports from
`harness.services.skill_graph`.
"""

from __future__ import annotations

# 1. Models & Dataclasses (fundamental, zero internal dependencies)
from harness.services.skill_graph.models import (
    CANONICAL_PIPELINE_PRECEDENCE,
    ActionGateResult,
    AntiPatternNode,
    AntiPatternViolation,
    EdgeType,
    InvariantNode,
    InvariantViolation,
    SkillAntiPatternDefinition,
    SkillCardDefinition,
    SkillChainResult,
    SkillEdge,
    SkillExecutionGuidance,
    SkillInvariantDefinition,
    SkillNode,
    SkillStageDefinition,
    SkillTopologyReport,
    StageNode,
)

# 2. Protocols & ServiceKeys
from harness.services.skill_graph.protocols import (
    SKILL_GRAPH_KEY,
    SKILL_GRAPH_SERVICE_KEY,
    SKILL_INTELLIGENCE_KEY,
    SKILL_REGISTRY_KEY,
    SkillGraphService,
    SkillIntelligenceService,
    SkillRegistryService,
)

# 3. Routing & Algorithms
from harness.services.skill_graph.routing import (
    _would_create_cycle,
    compute_prerequisite_closure,
    find_shortest_path,
    would_create_cycle,
)

# 4. AST Guard & Card Parser
from harness.services.skill_graph.guard import AntiPatternGuard
from harness.services.skill_graph.card_parser import SkillCardParser

# 5. Indexer
from harness.services.skill_graph.indexer import SkillCatalogIndexer

# 6. Specialized Domain Engines
from harness.services.skill_graph.scanner import (
    link_knowledge_vault_items,
    scan_skills_catalog,
)
from harness.services.skill_graph.topology import (
    compute_skill_chain,
    compute_topology_report,
    evaluate_chain_feasibility,
)
from harness.services.skill_graph.intent import (
    _trigram_overlap,
    route_skill_intent,
)
from harness.services.skill_graph.guidance import (
    compile_execution_guidance_plan,
    export_html_brief,
)
from harness.services.skill_graph.adapter import SkillIntelligenceAdapter
from harness.services.skill_graph.plugin import SkillRegistryPlugin

# 7. Service implementations & factories
from harness.services.skill_graph.service import (
    BuiltinSkillGraphService,
    BuiltinSkillRegistryService,
    get_default_skill_graph,
    get_default_skill_registry,
    resolve_skill_intelligence,
)

# 8. Skill Clustering re-exports
from harness.services.skill_clustering import (
    SKILL_CLUSTERING_KEY,
    CrossClusterBridge,
    EmergentCapability,
    SkillCluster,
    SkillClusteringEngine,
    SkillClusteringService,
    SkillSelectionPlan,
)

__all__ = [
    # Models & Dataclasses
    "ActionGateResult",
    "AntiPatternNode",
    "AntiPatternViolation",
    "CANONICAL_PIPELINE_PRECEDENCE",
    "EdgeType",
    "InvariantNode",
    "InvariantViolation",
    "SkillAntiPatternDefinition",
    "SkillCardDefinition",
    "SkillCardParser",
    "SkillCatalogIndexer",
    "SkillChainResult",
    "SkillEdge",
    "SkillExecutionGuidance",
    "SkillInvariantDefinition",
    "SkillNode",
    "SkillStageDefinition",
    "SkillTopologyReport",
    "StageNode",
    # Protocols & ServiceKeys
    "SKILL_CLUSTERING_KEY",
    "SKILL_GRAPH_KEY",
    "SKILL_GRAPH_SERVICE_KEY",
    "SKILL_INTELLIGENCE_KEY",
    "SKILL_REGISTRY_KEY",
    "SkillGraphService",
    "SkillIntelligenceService",
    "SkillRegistryService",
    # Service Implementations & Factories
    "BuiltinSkillGraphService",
    "BuiltinSkillRegistryService",
    "SkillIntelligenceAdapter",
    "SkillRegistryPlugin",
    "get_default_skill_graph",
    "get_default_skill_registry",
    "resolve_skill_intelligence",
    # Clustering
    "CrossClusterBridge",
    "EmergentCapability",
    "SkillCluster",
    "SkillClusteringEngine",
    "SkillClusteringService",
    "SkillSelectionPlan",
    # Routing & Traversal
    "_would_create_cycle",
    "compute_prerequisite_closure",
    "compute_skill_chain",
    "compute_topology_report",
    "evaluate_chain_feasibility",
    "find_shortest_path",
    "link_knowledge_vault_items",
    "route_skill_intent",
    "scan_skills_catalog",
    "would_create_cycle",
    # Guidance
    "compile_execution_guidance_plan",
    "export_html_brief",
]
