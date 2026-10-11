"""Recursive pure-language Tree-Sitter style Bash AST decompilation and subshell extraction."""

from __future__ import annotations

import re
import shlex
import sys
from typing import Any

from harness.services.kimi_bridge import BashAstNode

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def _extract_nested_constructs(text: str) -> tuple[str, list[dict[str, Any]]]:
    """Extract subshells $(cmd), `cmd`, and process substitutions <(cmd), >(cmd)."""
    subshells: list[dict[str, Any]] = []
    cleaned = text

    # 1. Match $(...) subshells
    dollar_sub_pattern = r"\$\((.*?)\)"
    for m in re.finditer(dollar_sub_pattern, text):
        raw_match = m.group(0)
        inner = m.group(1).strip()
        if inner:
            subshells.append({
                "type": "subshell",
                "raw": raw_match,
                "command": inner,
                "span": m.span(),
            })

    # 2. Match `...` backtick subshells
    backtick_pattern = r"`(.*?)`"
    for m in re.finditer(backtick_pattern, text):
        raw_match = m.group(0)
        inner = m.group(1).strip()
        if inner:
            subshells.append({
                "type": "subshell",
                "raw": raw_match,
                "command": inner,
                "span": m.span(),
            })

    # 3. Match <(...) and >(...) process substitutions
    proc_sub_pattern = r"[<>]\((.*?)\)"
    for m in re.finditer(proc_sub_pattern, text):
        raw_match = m.group(0)
        inner = m.group(1).strip()
        if inner:
            subshells.append({
                "type": "process_substitution",
                "raw": raw_match,
                "command": inner,
                "span": m.span(),
            })

    return cleaned, subshells


def parse_bash_ast(command_str: str) -> BashAstNode:
    """Recursive pure-language Tree-Sitter style Bash AST parser.

    Decomposes commands, chained operators (&&, ||, ;, |), redirections,
    environment variables, subshells, and process substitutions into a hierarchical BashAstNode tree.
    """
    clean_cmd = command_str.strip()
    if not clean_cmd:
        return BashAstNode(
            node_type="command",
            raw="",
            binary="",
            arguments=(),
            verdict="allow",
            reason="Empty command",
        )

    # Check for chained operators at current level
    operator_regex = r"(&&|\|\||;|\|)"
    raw_segments = re.split(operator_regex, clean_cmd)

    if len(raw_segments) > 1:
        child_nodes: list[BashAstNode] = []
        operators: list[str] = []

        for seg in raw_segments:
            s = seg.strip()
            if not s:
                continue
            if s in ("&&", "||", ";", "|"):
                operators.append(s)
            else:
                child_nodes.append(parse_bash_ast(s))

        node_type = "pipeline" if all(op == "|" for op in operators) else "compound"
        return BashAstNode(
            node_type=node_type,
            raw=clean_cmd,
            binary=child_nodes[0].binary if child_nodes else "",
            arguments=child_nodes[0].arguments if child_nodes else (),
            operators=tuple(operators),
            children=tuple(child_nodes),
            span=(0, len(clean_cmd)),
        )

    # Single command segment - extract subshells / process substitutions
    _, nested_constructs = _extract_nested_constructs(clean_cmd)

    try:
        tokens = shlex.split(clean_cmd, posix=True)
    except ValueError:
        tokens = clean_cmd.split()

    variables: list[tuple[str, str]] = []
    args: list[str] = []
    redirs: list[str] = []
    binary = ""

    idx = 0
    while idx < len(tokens):
        tok = tokens[idx]
        if "=" in tok and not binary and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tok):
            k, v = tok.split("=", 1)
            variables.append((k, v))
            idx += 1
        else:
            break

    if idx < len(tokens):
        binary = tokens[idx]
        idx += 1

    while idx < len(tokens):
        tok = tokens[idx]
        if tok.startswith(("<", ">", ">>", "2>", "2>&1", "&>")):
            redirs.append(tok)
        else:
            args.append(tok)
        idx += 1

    nested_nodes: list[BashAstNode] = []
    for sc in nested_constructs:
        child_ast = parse_bash_ast(sc["command"])
        nested_nodes.append(
            BashAstNode(
                node_type=sc["type"],
                raw=sc["raw"],
                binary=child_ast.binary,
                arguments=child_ast.arguments,
                children=child_ast.children,
                span=sc["span"],
            )
        )

    return BashAstNode(
        node_type="command",
        raw=clean_cmd,
        binary=binary,
        arguments=tuple(args),
        redirections=tuple(redirs),
        variables=tuple(variables),
        children=tuple(nested_nodes),
        span=(0, len(clean_cmd)),
    )


__all__ = [
    "_extract_nested_constructs",
    "parse_bash_ast",
]
