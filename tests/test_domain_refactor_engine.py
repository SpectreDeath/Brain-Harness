"""Tests for Domain 4: Refactor Engine plugin."""

from __future__ import annotations

import pytest

from plugins.refactor_engine.main import (
    extract_function_preview,
    find_unused_functions,
)


@pytest.mark.unit
class TestRefactorEnginePlugin:
    def test_find_unused_functions(self) -> None:
        code = (
            "def used_func():\n"
            "    return 1\n\n"
            "def dead_func():\n"
            "    return 2\n\n"
            "def main():\n"
            "    used_func()\n"
        )
        res = find_unused_functions(code)
        assert res["status"] == "ok"
        unused_names = [f["name"] for f in res["unused_functions"]]
        assert "dead_func" in unused_names
        assert "used_func" not in unused_names

    def test_extract_function_preview(self) -> None:
        code = (
            "def process():\n"
            "    a = 10\n"
            "    b = 20\n"
            "    c = a + b\n"
        )
        res = extract_function_preview(code, start_line=2, end_line=3, new_func_name="compute_values")
        assert res["status"] == "ok"
        assert "def compute_values():" in res["refactored_preview"]
