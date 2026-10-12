"""Protocols and service keys for context compiler."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from harness.kernel.context import ServiceKey


@runtime_checkable
class ContextCompilerProtocol(Protocol):
    """Protocol for 3-tier AST context compilation."""

    def compile(self, target_file: str | Path) -> object: ...


CONTEXT_COMPILER_KEY = ServiceKey[ContextCompilerProtocol]("compiler.context_compiler")
