"""Migration Assistant plugin — Pydantic v2 and Python 3.10+ modern syntax migration checker."""

from __future__ import annotations

import re
from typing import Any


def check_pydantic_v2_readiness(code: str) -> dict[str, Any]:
    """Scan Python code for deprecated Pydantic v1 patterns."""
    issues: list[dict[str, Any]] = []

    lines = code.splitlines()
    for line_num, line in enumerate(lines, start=1):
        if re.search(r"class\s+Config\s*:", line):
            issues.append({
                "rule": "PydanticV1ConfigClass",
                "severity": "high",
                "line": line_num,
                "detail": "Replace 'class Config:' with 'model_config = ConfigDict(...)' in Pydantic v2.",
            })

        if re.search(r"@validator\(", line):
            issues.append({
                "rule": "PydanticV1ValidatorDecorator",
                "severity": "high",
                "line": line_num,
                "detail": "Replace '@validator' with '@field_validator' in Pydantic v2.",
            })

        if re.search(r"@root_validator\(", line):
            issues.append({
                "rule": "PydanticV1RootValidatorDecorator",
                "severity": "high",
                "line": line_num,
                "detail": "Replace '@root_validator' with '@model_validator' in Pydantic v2.",
            })

        if re.search(r"\.dict\(", line):
            issues.append({
                "rule": "PydanticV1DictMethod",
                "severity": "medium",
                "line": line_num,
                "detail": "Replace '.dict()' with '.model_dump()' in Pydantic v2.",
            })

        if re.search(r"\.parse_obj\(", line):
            issues.append({
                "rule": "PydanticV1ParseObjMethod",
                "severity": "medium",
                "line": line_num,
                "detail": "Replace '.parse_obj()' with '.model_validate()' in Pydantic v2.",
            })

    return {
        "status": "ok",
        "ready_for_v2": len(issues) == 0,
        "deprecated_patterns_count": len(issues),
        "issues": issues,
    }


def check_python_version_compat(code: str) -> dict[str, Any]:
    """Scan for pre-Python 3.10 legacy patterns."""
    suggestions: list[dict[str, Any]] = []
    lines = code.splitlines()

    for line_num, line in enumerate(lines, start=1):
        if "from typing import Union" in line or re.search(r"\bUnion\[", line):
            suggestions.append({
                "rule": "LegacyUnionSyntax",
                "line": line_num,
                "suggestion": "Replace Union[A, B] with modern PEP 604 union syntax: 'A | B'.",
            })

        if "from typing import Optional" in line or re.search(r"\bOptional\[", line):
            suggestions.append({
                "rule": "LegacyOptionalSyntax",
                "line": line_num,
                "suggestion": "Replace Optional[T] with modern union syntax: 'T | None'.",
            })

        if "import distutils" in line or "from distutils" in line:
            suggestions.append({
                "rule": "RemovedDistutils",
                "line": line_num,
                "suggestion": "distutils was removed in Python 3.12. Replace with packaging or setuptools.",
            })

    return {
        "status": "ok",
        "modern_python_compliant": len(suggestions) == 0,
        "suggestions_count": len(suggestions),
        "suggestions": suggestions,
    }
