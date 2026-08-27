"""Tests for context compilation, optimization commands, and polyglot skeletonizer registry."""

import pytest
from pathlib import Path

from harness.commands import CommandRegistry
from harness.commands.context import (
    compile_context_cmd,
    optimize_context_cmd,
    skeletonize_code_cmd,
)
from plugins.memory_and_epistemics.context_compiler.compiler_core import (
    SkeletonizerRegistry,
)


@pytest.mark.asyncio
async def test_skeletonize_code_cmd():
    py_code = """
import os

def calculate_metric(a: int, b: int) -> int:
    \"\"\"Calculate basic sum.\"\"\"
    x = a * 2
    y = b * 3
    return x + y

class DataProcessor:
    def process(self, data: list) -> list:
        \"\"\"Process records.\"\"\"
        results = []
        for d in data:
            results.append(d.strip())
        return results
"""
    res = await skeletonize_code_cmd(py_code)
    assert res.functions_stripped == 2
    assert "def calculate_metric" in res.skeleton_code
    assert '"""Calculate basic sum."""' in res.skeleton_code
    assert "class DataProcessor:" in res.skeleton_code
    assert res.reduction_pct > 0


def test_polyglot_skeletonizer_registry(tmp_path: Path):
    # 1. Test JSON
    json_text = '{"name": "test_app", "version": "1.0", "dependencies": ["dep1", "dep2", "dep3", "dep4"], "nested": {"a": 1, "b": 2}}'
    json_skel, _ = SkeletonizerRegistry.skeletonize_json(json_text)
    assert "name" in json_skel
    assert "nested" in json_skel

    # 2. Test Markdown
    md_text = """# Main Heading

This is a long introductory paragraph that has a lot of narrative details.

## Section 1: Architecture
- Point A
- Point B

Some other explanatory text that should be omitted in structural skeleton.

### Subsection 1.1: Seams
```python
def foo(): pass
```
"""
    md_skel, stripped = SkeletonizerRegistry.skeletonize_markdown(md_text)
    assert "# Main Heading" in md_skel
    assert "## Section 1: Architecture" in md_skel
    assert "- Point A" in md_skel
    assert "### Subsection 1.1: Seams" in md_skel
    assert stripped > 0

    # 3. Test generic file routing
    py_file = tmp_path / "mod.py"
    py_file.write_text("def run():\n    return 42\n", encoding="utf-8")
    skel_py, _ = SkeletonizerRegistry.skeletonize(py_file)
    assert "def run" in skel_py

    json_file = tmp_path / "data.json"
    json_file.write_text(json_text, encoding="utf-8")
    skel_json, _ = SkeletonizerRegistry.skeletonize(json_file)
    assert "name" in skel_json


@pytest.mark.asyncio
async def test_compile_context_cmd(tmp_path: Path):
    # Create a small simulated project
    main_py = tmp_path / "main.py"
    util_py = tmp_path / "util.py"
    readme_md = tmp_path / "README.md"

    util_py.write_text(
        "def compute_helper(x: int) -> int:\n    \"\"\"Docstring.\"\"\"\n    return x * 10\n",
        encoding="utf-8",
    )
    main_py.write_text(
        "from util import compute_helper\n\ndef main():\n    return compute_helper(5)\n",
        encoding="utf-8",
    )
    readme_md.write_text("# Project Docs\n\nDetailed descriptions.\n", encoding="utf-8")

    res = await compile_context_cmd(target_file=main_py, repo_root=tmp_path)
    assert res.target_file == str(main_py.resolve())
    assert res.tier1_files == 1
    assert res.compiled_tokens > 0
    assert "FULL SOURCE" in res.assembled_prompt


@pytest.mark.asyncio
async def test_optimize_context_cmd():
    messages = [
        {"id": "m1", "role": "system", "content": "You are a helpful assistant", "turn": 0},
        {"id": "m2", "role": "user", "content": "Solve task 1", "turn": 0},
        {"id": "m3", "role": "assistant", "content": "Calling tool", "turn": 1},
        {"id": "m4", "role": "user", "content": "Tool output data", "turn": 1},
    ]

    res = await optimize_context_cmd(session_id="test_opt_sess", messages=messages)
    assert res.session_id == "test_opt_sess"
    assert res.input_messages == 4
    assert res.final_messages > 0
    assert len(res.assembled_prompt) > 0


@pytest.mark.asyncio
async def test_context_command_registry_dispatch():
    desc_compile = CommandRegistry.get("context.compile")
    assert desc_compile is not None
    assert desc_compile.category == "context"

    desc_opt = CommandRegistry.get("context.optimize")
    assert desc_opt is not None

    desc_skel = CommandRegistry.get("context.skeletonize")
    assert desc_skel is not None

    # Test dispatch
    skel_res = await CommandRegistry.dispatch("context.skeletonize", source_or_file="def test():\n    return 1\n")
    assert skel_res.functions_stripped == 1
