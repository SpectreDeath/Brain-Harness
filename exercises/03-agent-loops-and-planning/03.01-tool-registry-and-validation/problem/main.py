"""Exercise 03.01: Tool Registry and Schema Validation (Problem)."""

from __future__ import annotations

from typing import Any

from harness.services.tools import ToolRegistry


async def run_tool_registration_demo() -> dict[str, Any]:
    registry = ToolRegistry()  # noqa: F841

    # TODO: Register tool "text.concat" that concatenates `str1` and `str2` with a space
    # TODO: Invoke "text.concat" with {"str1": "Hello", "str2": "Harness"}
    # TODO: Return result

    raise NotImplementedError
