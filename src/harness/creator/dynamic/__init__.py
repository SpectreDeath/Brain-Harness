"""Creator mode — in-memory plugin building, hot-reloading, and project export.

Inspired by DeepSeek Harness's Creator Mode presets, this allows:
    1. In-memory plugin construction from raw Python code or functions
    2. Automatic AST parameter extraction and manifest inference
    3. Live hot-reloading of dynamic in-memory tools
    4. 1-line bidirectional export to scaffolded on-disk projects
    5. Interactive scaffolding of new plugins
    6. Live runtime introspection of the service dependency graph
"""

from __future__ import annotations

from harness.creator.dynamic.builder import (
    DynamicPluginBuilder,
    resolve_dynamic_builder,
)
from harness.creator.dynamic.compiler import _compile_dynamic_module
from harness.creator.dynamic.inspector import ASTFunctionInspector
from harness.creator.dynamic.models import FunctionSignatureMetadata
from harness.creator.dynamic.plugin import DynamicPythonPlugin
from harness.creator.introspection import RuntimeIntrospector

__all__ = [
    "ASTFunctionInspector",
    "DynamicPluginBuilder",
    "DynamicPythonPlugin",
    "FunctionSignatureMetadata",
    "RuntimeIntrospector",
    "_compile_dynamic_module",
    "resolve_dynamic_builder",
]
