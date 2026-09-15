"""Test suite for Deepened AST Refactor Engine and Automated Code Repair."""

import pytest

from harness.kernel.context import ServiceContext
from harness.services.refactor_engine import (
    REFACTOR_ENGINE_KEY,
    RefactorEngineService,
)
from plugins.software_engineering.refactor_engine.main import (
    RefactorEnginePlugin,
    convert_to_slotted_dataclass,
    flatten_nested_ifs,
    plugin,
)


def test_plugin_singleton_and_manifest():
    assert isinstance(plugin, RefactorEnginePlugin)
    assert plugin.name == "plugin.refactor_engine"
    assert REFACTOR_ENGINE_KEY in plugin.provides


@pytest.mark.asyncio
async def test_ioc_registration():
    ctx = ServiceContext()
    p = RefactorEnginePlugin()
    await p.on_load(ctx)

    service = ctx.require(REFACTOR_ENGINE_KEY)
    assert isinstance(service, RefactorEngineService)


def test_flatten_nested_ifs_sim102():
    snippet = """
def process(node):
    if isinstance(node, dict):
        if "environ" in node:
            return node["environ"]
    return None
"""
    res = flatten_nested_ifs(snippet)
    assert res.status == "ok"
    assert res.transforms_applied == 1
    assert "if isinstance(node, dict) and 'environ' in node:" in res.refactored_code


def test_flatten_nested_ifs_triple_nested():
    snippet = """
if a:
    if b:
        if c:
            do_work()
"""
    res = flatten_nested_ifs(snippet)
    assert res.status == "ok"
    assert res.transforms_applied == 2
    assert "if a and b and c:" in res.refactored_code


def test_convert_to_slotted_dataclass():
    snippet = """
class UserProfile:
    name: str
    age: int
"""
    res = convert_to_slotted_dataclass(snippet, "UserProfile")
    assert res.status == "ok"
    assert "@dataclass(slots=True, frozen=True)" in res.refactored_code
    assert "from dataclasses import dataclass" in res.refactored_code


def test_auto_remediate_diagnostics():
    p = RefactorEnginePlugin()
    snippet = """
if x > 0:
    if y > 0:
        return True
"""
    diagnostics = [{"rule": "SIM102", "message": "Use a single if statement"}]
    res = p.auto_remediate_diagnostics(snippet, diagnostics)
    assert res.status == "ok"
    assert "if x > 0 and y > 0:" in res.refactored_code
