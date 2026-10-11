"""CellCog Multimodal Sub-Agent Service — modular subpackage facade."""

from __future__ import annotations

from harness.services.cellcog.catalog import CELLCOG_CATALOG
from harness.services.cellcog.execution import execute_cellcog_research, execute_cellcog_task
from harness.services.cellcog.compiler import (
    MultimodalProtocolCompiler,
    parse_generate_file_tags,
    parse_show_file_tags,
)
from harness.services.cellcog.models import (
    DEFAULT_AGENT_PROVIDER,
    DEFAULT_CHAT_MODE,
    DEFAULT_CHAT_TIER,
    DEFAULT_RESEARCH_TIMEOUT_SEC,
    DEFAULT_TIMEOUT_SEC,
    ENV_CELLCOG_API_KEY,
    MAX_ATTACHMENT_SIZE_BYTES,
    SENSITIVE_FILE_PATTERNS,
    CellCogArtifact,
    CellCogCapabilitiesResult,
    CellCogCapabilityItem,
    CellCogResearchResult,
    CellCogRunResult,
    MultimodalCompilationResult,
    infer_mime_type,
)
from harness.services.cellcog.protocols import CELLCOG_SERVICE_KEY, CellCogServiceProtocol
from harness.services.cellcog.resolvers import resolve_cellcog_service
from harness.services.cellcog.service import CellCogService

__all__ = [
    "CELLCOG_CATALOG",
    "execute_cellcog_research",
    "execute_cellcog_task",
    "CELLCOG_SERVICE_KEY",
    "DEFAULT_AGENT_PROVIDER",
    "DEFAULT_CHAT_MODE",
    "DEFAULT_CHAT_TIER",
    "DEFAULT_RESEARCH_TIMEOUT_SEC",
    "DEFAULT_TIMEOUT_SEC",
    "ENV_CELLCOG_API_KEY",
    "MAX_ATTACHMENT_SIZE_BYTES",
    "SENSITIVE_FILE_PATTERNS",
    "CellCogArtifact",
    "CellCogCapabilitiesResult",
    "CellCogCapabilityItem",
    "CellCogResearchResult",
    "CellCogRunResult",
    "CellCogService",
    "CellCogServiceProtocol",
    "MultimodalCompilationResult",
    "MultimodalProtocolCompiler",
    "infer_mime_type",
    "parse_generate_file_tags",
    "parse_show_file_tags",
    "resolve_cellcog_service",
]
