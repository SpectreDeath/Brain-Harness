"""3-tier AST context compilation engine subpackage (decomposed)."""

from __future__ import annotations

from plugins.memory_and_epistemics.context_compiler.compiler_core.compiler import ContextCompiler
from plugins.memory_and_epistemics.context_compiler.compiler_core.constants import (
    CHARS_PER_TOKEN,
    KNOWN_EVENT_DECORATORS,
    _BUILTIN_NAMES,
    estimate_tokens,
)
from plugins.memory_and_epistemics.context_compiler.compiler_core.models import (
    CompiledContext,
    FileSymbols,
    ReachabilityResult,
    TierEntry,
)
from plugins.memory_and_epistemics.context_compiler.compiler_core.module_index import ModuleIndex
from plugins.memory_and_epistemics.context_compiler.compiler_core.protocols import (
    CONTEXT_COMPILER_KEY,
    ContextCompilerProtocol,
)
from plugins.memory_and_epistemics.context_compiler.compiler_core.resolvers import resolve_context_compiler
from plugins.memory_and_epistemics.context_compiler.compiler_core.skeletonizer import (
    CodeSkeletonizer,
    SkeletonizerRegistry,
    skeletonize_source,
)
from plugins.memory_and_epistemics.context_compiler.compiler_core.symbol_resolver import (
    SymbolResolver,
    extract_symbols,
)

__all__ = [
    "CHARS_PER_TOKEN",
    "CONTEXT_COMPILER_KEY",
    "CodeSkeletonizer",
    "CompiledContext",
    "ContextCompiler",
    "ContextCompilerProtocol",
    "FileSymbols",
    "KNOWN_EVENT_DECORATORS",
    "ModuleIndex",
    "ReachabilityResult",
    "SkeletonizerRegistry",
    "SymbolResolver",
    "TierEntry",
    "_BUILTIN_NAMES",
    "estimate_tokens",
    "extract_symbols",
    "resolve_context_compiler",
    "skeletonize_source",
]
