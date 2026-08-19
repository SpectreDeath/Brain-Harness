"""Exercise 03.01: Tool Registry and Schema Validation (Solution)."""

from __future__ import annotations

from typing import Any

from harness.services.tools import ToolRegistry


async def run_tool_registration_demo() -> dict[str, Any]:
    registry = ToolRegistry()

    registry.register(
        name="text.concat",
        description="Concatenate two strings with space",
        executor=lambda str1="", str2="": f"{str1} {str2}".strip(),
        parameters_schema={
            "type": "object",
            "properties": {
                "str1": {"type": "string"},
                "str2": {"type": "string"},
            },
            "required": ["str1", "str2"],
        },
    )

    return await registry.invoke("text.concat", {"str1": "Hello", "str2": "Harness"})
