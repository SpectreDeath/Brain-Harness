"""Tests for Domain: Context Compiler plugin (3-Tier AST Token-Pruning Compiler)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from harness.creator.validator import PluginValidator
from plugins.memory_and_epistemics.context_compiler.compiler_core import (
    CodeSkeletonizer,
    ContextCompiler,
    ModuleIndex,
    SymbolResolver,
    estimate_tokens,
    skeletonize_source,
)
from plugins.memory_and_epistemics.context_compiler.main import (
    ContextCompilerService,
    compile_context,
    estimate_token_reduction,
    resolve_reachability,
    skeletonize_code,
)


@pytest.mark.unit
class TestContextCompilerPlugin:
    def test_skeletonize_source_strips_bodies(self) -> None:
        source = '''
import os

def calculate_metric(a: int, b: int) -> int:
    """Calculate the metric."""
    intermediate = a * 2
    return intermediate + b

class Helper:
    """Helper class."""
    def run(self, val: str) -> bool:
        """Run the helper."""
        return len(val) > 0
'''
        skeleton, count = skeletonize_source(source)
        assert count == 2
        assert "intermediate = a * 2" not in skeleton
        assert "return intermediate + b" not in skeleton
        assert "Calculate the metric." in skeleton
        assert "Helper class." in skeleton
        assert "def calculate_metric(a: int, b: int) -> int:" in skeleton
        assert "..." in skeleton

    def test_skeletonize_code_tool(self) -> None:
        res = skeletonize_code("def foo():\n    '''doc'''\n    return 42")
        assert res["status"] == "ok"
        assert res["functions_stripped"] == 1
        assert "..." in res["skeleton_code"]
        assert res["original_tokens"] >= res["skeleton_tokens"]

    def test_end_to_end_context_compilation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Module A
            mod_a = root / "mod_a.py"
            mod_a.write_text("""
def helper_a():
    '''Helper A docstring.'''
    step1 = 1 + 2
    return step1
""", encoding="utf-8")

            # Module B (imports A)
            mod_b = root / "mod_b.py"
            mod_b.write_text("""
import mod_a

def main_job():
    '''Main job docstring.'''
    val = mod_a.helper_a()
    return val * 10
""", encoding="utf-8")

            # Module C (unrelated / excluded)
            mod_c = root / "mod_c.py"
            mod_c.write_text("""
def unrelated():
    '''Unrelated docstring.'''
    return 999
""", encoding="utf-8")

            res = compile_context(str(root), "mod_b.py", max_hops=2)
            assert res["status"] == "ok"
            assert res["total_repo_files"] == 3
            assert res["tier1_count"] == 1
            assert res["tier2_count"] == 1  # mod_a
            assert res["tier3_excluded_count"] == 1  # mod_c
            assert "FULL SOURCE" in res["prompt_text"]
            assert "SKELETON" in res["prompt_text"]
            assert "Helper A docstring." in res["prompt_text"]
            assert "step1 = 1 + 2" not in res["prompt_text"]  # stripped!

            # Test reachability tool
            reach = resolve_reachability(str(root), "mod_b.py", max_hops=2)
            assert reach["status"] == "ok"
            assert reach["reachable_file_count"] == 1

            # Test estimate reduction tool
            est = estimate_token_reduction(str(root), "mod_b.py", max_hops=2)
            assert est["status"] == "ok"
            assert est["tokens_saved"] > 0

    def test_service_wrapper(self) -> None:
        svc = ContextCompilerService()
        res = svc.skeletonize("def test_fn():\n    return True")
        assert res["status"] == "ok"

    @pytest.mark.asyncio
    async def test_plugin_validator_compliance(self) -> None:
        plugin_dir = Path("plugins/memory_and_epistemics/context_compiler")
        report = await PluginValidator.validate(plugin_dir)
        assert report.valid, f"Validation errors: {report.errors}"
        assert len(report.errors) == 0

