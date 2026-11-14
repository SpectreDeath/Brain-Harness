"""Endogenous reflection CLI command and Knowledge Vault management package."""

from __future__ import annotations

from harness.creator.reflection import (
    HarnessReflectorEngine,
    MemoryPatternPipeline,
    ReflectionReport,
    ReflectionScope,
    resolve_reflector_engine,
)
from harness.services.storage import (
    SQLiteStorageService,
    audit_vault_hygiene,
    backfill_edges_mechanically,
    export_knowledge_graph,
    resolve_knowledge_graph_service,
    suggest_category_for_item,
    suggest_tags_for_item,
    validate_export_path,
)
from .group import knowledge_group, logger
from .runner import (
    run_reflection_cmd,
    knowledge_reflect,
    reflect_cli,
)
from .vault_cmds import (
    knowledge_sync,
    knowledge_list,
    knowledge_query,
    knowledge_joint_query,
    knowledge_verify,
)
from .export_cmds import (
    knowledge_export,
    knowledge_backfill,
)
from .lifecycle_cmds import (
    knowledge_lifecycle,
    knowledge_resolve,
)
from .lineage_cmds import (
    knowledge_contradictions,
    knowledge_lineage,
)
from .graph_cmds import (
    knowledge_neighbors,
    knowledge_path,
    knowledge_topic,
    knowledge_dependents,
    knowledge_orphans,
)
from .hygiene_cmds import (
    knowledge_stats,
    knowledge_hygiene,
)
from .timeline_cmds import (
    knowledge_timeline,
)

__all__ = [
    "knowledge_backfill",
    "knowledge_contradictions",
    "knowledge_dependents",
    "knowledge_export",
    "knowledge_group",
    "knowledge_hygiene",
    "knowledge_lifecycle",
    "knowledge_lineage",
    "knowledge_list",
    "knowledge_neighbors",
    "knowledge_orphans",
    "knowledge_path",
    "knowledge_query",
    "knowledge_reflect",
    "knowledge_resolve",
    "knowledge_stats",
    "knowledge_sync",
    "knowledge_timeline",
    "knowledge_topic",
    "knowledge_verify",
    "reflect_cli",
    "run_reflection_cmd",
]
