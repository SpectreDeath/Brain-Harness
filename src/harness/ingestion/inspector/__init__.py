"""Repo inspector — analyzes downloaded repositories and synthesizes manifests."""

from __future__ import annotations

from harness.ingestion.inspector.ast_extractor import (
    extract_function_params,
    extract_python_entrypoints,
    guess_entrypoint,
    read_requirements,
    try_python_ast,
)
from harness.ingestion.inspector.exceptions import InspectionError
from harness.ingestion.inspector.inspector import RepoInspector
from harness.ingestion.inspector.js_ts_extractor import (
    extract_js_ts_entrypoints,
    try_js_ts_inspection,
)
from harness.ingestion.inspector.manifest_strategies import (
    convert_mcp_json,
    derive_plugin_name,
    try_mcp_json,
    try_package_json,
    try_plugin_json,
    try_pyproject,
)
from harness.ingestion.inspector.skills_bundle import (
    parse_skill_frontmatter,
    try_skills_bundle,
)

__all__ = [
    "InspectionError",
    "RepoInspector",
    "convert_mcp_json",
    "derive_plugin_name",
    "extract_function_params",
    "extract_js_ts_entrypoints",
    "extract_python_entrypoints",
    "guess_entrypoint",
    "parse_skill_frontmatter",
    "read_requirements",
    "try_js_ts_inspection",
    "try_mcp_json",
    "try_package_json",
    "try_plugin_json",
    "try_pyproject",
    "try_python_ast",
    "try_skills_bundle",
]
