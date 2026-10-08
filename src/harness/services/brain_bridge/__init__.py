"""Brain Bridge and Repository Attachment service package.

Elevates external brain inspection, TF-IDF vector retrieval, format detection,
and Git repository mounting into a deep micro-kernel service.

Adheres to:
- Rule 1: Everything is a plugin.
- Rule 2: Typed service keys (BRAIN_BRIDGE_KEY).
- Rule 12: Slotted and frozen dataclass architecture.
- Rule 49: Skill-to-IoC micro-kernel seam elevation.
- Rule 58: Single-seam resolver factory (resolve_brain_bridge).
"""

from __future__ import annotations

from .core import DefaultBrainBridgeService
from .detector import clone_remote_repo, detect_brain_format, is_git_url
from .indexers import index_text_files, parse_git_commits, parse_transcripts
from .models import (
    BrainAttachResult,
    BrainDetachResult,
    BrainListResult,
    BrainMountRecord,
    BrainQueryResult,
    IndexedChunk,
    SearchScoreMatch,
    TrajectoryEntry,
)
from .protocols import BRAIN_BRIDGE_KEY, BrainBridgeService
from .resolvers import resolve_brain_bridge
from .tokenizers import (
    DEFAULT_CODE_EXTS,
    SPECIAL_FILENAMES,
    compute_tf_idf_vector,
    tokenize_text,
)

__all__ = [
    "BRAIN_BRIDGE_KEY",
    "BrainAttachResult",
    "BrainBridgeService",
    "BrainDetachResult",
    "BrainListResult",
    "BrainMountRecord",
    "BrainQueryResult",
    "DEFAULT_CODE_EXTS",
    "DefaultBrainBridgeService",
    "IndexedChunk",
    "SPECIAL_FILENAMES",
    "SearchScoreMatch",
    "TrajectoryEntry",
    "clone_remote_repo",
    "compute_tf_idf_vector",
    "detect_brain_format",
    "index_text_files",
    "is_git_url",
    "parse_git_commits",
    "parse_transcripts",
    "resolve_brain_bridge",
    "tokenize_text",
]
