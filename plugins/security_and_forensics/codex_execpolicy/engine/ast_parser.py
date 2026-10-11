"""AST parser and tokenizer facade for Codex ExecPolicy."""

from __future__ import annotations

import sys

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from plugins.security_and_forensics.codex_execpolicy.engine.ast_core import (
    _extract_nested_constructs,
    parse_bash_ast,
)
from plugins.security_and_forensics.codex_execpolicy.engine.tokenizer import (
    _tokenize_command,
    tokenize_shell_ast,
)

__all__ = [
    "_extract_nested_constructs",
    "_tokenize_command",
    "parse_bash_ast",
    "tokenize_shell_ast",
]
