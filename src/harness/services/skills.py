"""Unified Skill Subsystem — Authoritative composite entrypoint (Rule 18, Rule 49, Rule 58).

Unifies the partitioned skill architecture into a cohesive facade:
1. Parsing & Extraction (`harness.services.skill_parser`):
   Parses `CARD.md` single-pipe boxes and `SKILL.md` frontmatter/anti-patterns.
2. Knowledge Graph & Routing (`harness.services.skill_graph`):
   Directed acyclic dependency graph, shortest-path BFS routing, and dynamic guidance.
3. Clustering & Patterns (`harness.services.skill_clustering`):
   Semantic/topological clustering, macro-bridges, and task selection plans.
4. Visualization (`harness.services.skill_visualizer`):
   Dark-mode HTML Visual Brief reports generated in %TEMP%.
5. Pipeline Engine (`harness.services.skill_pipeline`):
   Multi-stage driver execution and telemetry reporting.
6. Unified Intelligence (`SkillIntelligenceService` & `SkillIntelligenceAdapter`):
   Authoritative composite protocol unifying discovery, topology, routing, and clustering (Rule 58).
"""

from __future__ import annotations

import sys

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# 1. Protocols & ServiceKeys
from harness.services.skill_graph import (
    SKILL_GRAPH_KEY,
    SKILL_GRAPH_SERVICE_KEY,
    SKILL_INTELLIGENCE_KEY,
    SKILL_REGISTRY_KEY,
    SkillGraphService,
    SkillIntelligenceService,
    SkillRegistryService,
    resolve_skill_graph_service,
    resolve_skill_intelligence_service,
)
from harness.services.skill_parser import (
    SKILL_PARSER_SERVICE_KEY,
    SkillCardParserService,
    parse_skill_card,
    parse_skill_markdown,
)
from harness.services.skill_clustering import (
    SKILL_CLUSTERING_SERVICE_KEY,
    SkillCluster,
    SkillClusteringService,
    SkillSelectionPlan,
)
from harness.services.skill_pipeline import (
    BaseSkillPipelineEngine,
    SkillPipelineReport,
    SkillStageResult,
)
from harness.services.skill_visualizer import SkillGraphVisualizer

# 2. Slotted Domain Models
from harness.services.skill_graph.models import (
    ActionGateResult,
    AntiPatternViolation,
    SkillCardDefinition,
    SkillChainResult,
    SkillExecutionGuidance,
    SkillTopologyReport,
)

# 3. Adapters & Guards
from harness.services.skill_graph.adapter import SkillIntelligenceAdapter
from harness.services.skill_graph.guard import AntiPatternGuard

__all__ = [
    # Keys
    "SKILL_CLUSTERING_SERVICE_KEY",
    "SKILL_GRAPH_KEY",
    "SKILL_GRAPH_SERVICE_KEY",
    "SKILL_INTELLIGENCE_KEY",
    "SKILL_PARSER_SERVICE_KEY",
    "SKILL_REGISTRY_KEY",
    # Protocols
    "SkillClusteringService",
    "SkillGraphService",
    "SkillIntelligenceService",
    "SkillRegistryService",
    "SkillCardParserService",
    # Models
    "ActionGateResult",
    "AntiPatternViolation",
    "SkillCardDefinition",
    "SkillChainResult",
    "SkillCluster",
    "SkillExecutionGuidance",
    "SkillPipelineReport",
    "SkillSelectionPlan",
    "SkillStageResult",
    "SkillTopologyReport",
    # Implementations & Tools
    "AntiPatternGuard",
    "BaseSkillPipelineEngine",
    "SkillGraphVisualizer",
    "SkillIntelligenceAdapter",
    # Functions
    "parse_skill_card",
    "parse_skill_markdown",
    "resolve_skill_graph_service",
    "resolve_skill_intelligence_service",
]
