"""Skill graph anti-pattern guard service package."""

from __future__ import annotations

from .ast_scanner import (
    extract_code_blocks,
    extract_combined_text,
    scan_blocked_calls,
    scan_code_ast,
)
from .formatter import format_self_repair_observation
from .guard import AntiPatternGuard
from .invariants import (
    check_rule15_credentials,
    check_rule30_powershell_glob,
    check_skill_invariants,
)
from .proposals import check_proposal_anti_patterns

__all__ = [
    "AntiPatternGuard",
    "check_proposal_anti_patterns",
    "check_rule15_credentials",
    "check_rule30_powershell_glob",
    "check_skill_invariants",
    "extract_code_blocks",
    "extract_combined_text",
    "format_self_repair_observation",
    "scan_blocked_calls",
    "scan_code_ast",
]
