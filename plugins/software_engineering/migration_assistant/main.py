"""Migration Assistant plugin — Pydantic v2 and Python 3.10+ modern syntax migration checker."""

from __future__ import annotations

import re
from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.migration_assistant import (
    MIGRATION_ASSISTANT_KEY,
    MigrationAssistantService,
    PydanticMigrationResult,
    PythonCompatResult,
)

logger = structlog.get_logger(__name__)


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


class MigrationAssistantPlugin(HarnessPlugin, MigrationAssistantService):
    """Harness Plugin providing Python and Pydantic migration analysis."""

    name = "plugin.migration_assistant"
    version = "1.0.0"
    description = "Python framework migration checker (Pydantic v1 to v2, Python 3.10+ union syntax)"
    trusted = True

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [MIGRATION_ASSISTANT_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(MIGRATION_ASSISTANT_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # MigrationAssistantService Protocol Implementation
    # -------------------------------------------------------------------------

    def check_pydantic_v2_readiness(self, code: str) -> PydanticMigrationResult:
        res = check_pydantic_v2_readiness(code=code)
        return PydanticMigrationResult(
            status=res["status"],
            ready_for_v2=res.get("ready_for_v2", True),
            deprecated_patterns_count=res.get("deprecated_patterns_count", 0),
            issues=res.get("issues", []),
            error=res.get("error"),
        )

    def check_python_version_compat(self, code: str) -> PythonCompatResult:
        res = check_python_version_compat(code=code)
        return PythonCompatResult(
            status=res["status"],
            modern_python_compliant=res.get("modern_python_compliant", True),
            suggestions_count=res.get("suggestions_count", 0),
            suggestions=res.get("suggestions", []),
            error=res.get("error"),
        )
