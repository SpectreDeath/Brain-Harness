"""AST syntax tree scanning and blocked call detection for agent action parameters."""

from __future__ import annotations

import ast
import json
import re
from typing import Any

from harness.services.skill_graph.models import AntiPatternViolation

BLOCKED_CALLS: frozenset[str] = frozenset({"eval", "exec", "input", "__import__"})


def extract_combined_text(action_name: str, action_input: dict[str, Any]) -> str:
    """Flatten action name and input parameters into combined searchable text."""
    text_parts: list[str] = [action_name]
    for val in action_input.values():
        if isinstance(val, str):
            text_parts.append(val)
        elif isinstance(val, (dict, list)):
            try:
                text_parts.append(json.dumps(val))
            except Exception:
                text_parts.append(str(val))
    return "\n".join(text_parts)


def extract_code_blocks(text: str) -> list[str]:
    """Extract fenced python codeblocks or fall back to full combined text."""
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)\n```", text, re.DOTALL)
    return blocks if blocks else [text]


def scan_code_ast(code_block: str, skill_name: str = "system_guard") -> list[AntiPatternViolation]:
    """Run AST visitor on code block to catch blocked library calls (eval, exec, input, __import__)."""
    violations: list[AntiPatternViolation] = []
    try:
        tree = ast.parse(code_block)
    except Exception:
        return violations

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            if func_name and func_name in BLOCKED_CALLS:
                violations.append(
                    AntiPatternViolation(
                        skill_name=skill_name,
                        anti_pattern=f"Blocked Call: {func_name}()",
                        symptom=f"Direct call to {func_name}() detected in proposed action parameters",
                        remedy="Use sandboxed execution or approved kernel tools instead",
                        matched_phrase=f"{func_name}()",
                    )
                )
    return violations


def scan_blocked_calls(combined_text: str, skill_name: str = "system_guard") -> list[AntiPatternViolation]:
    """Scan code blocks and raw text for blocked call patterns using AST and regex fallback."""
    violations: list[AntiPatternViolation] = []
    code_blocks = extract_code_blocks(combined_text)

    for block in code_blocks:
        violations.extend(scan_code_ast(block, skill_name=skill_name))

        # Fallback regex search for direct blocked call patterns (eval(...) etc.)
        for call in BLOCKED_CALLS:
            pattern = rf"(?:^|[^\w.]){re.escape(call)}\s*\("
            if re.search(pattern, block):
                match_already_found = any(call in v.anti_pattern for v in violations)
                if not match_already_found:
                    violations.append(
                        AntiPatternViolation(
                            skill_name=skill_name,
                            anti_pattern=f"Blocked Call: {call}()",
                            symptom=f"Direct invocation of {call}() detected in action input",
                            remedy="Use sandboxed execution or approved kernel tools instead",
                            matched_phrase=f"{call}()",
                        )
                    )

    return violations
