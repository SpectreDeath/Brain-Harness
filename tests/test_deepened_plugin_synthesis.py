"""Tests for the PluginSynthesisEngine, SynthesisRequest/Result, and CreatorPlugin."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from harness.creator.synthesis import (
    CREATOR_SERVICE_KEY,
    CreatorPlugin,
    PluginSynthesisEngine,
    SynthesisMode,
    SynthesisRequest,
    SynthesisResult,
)
from harness.kernel.context import ServiceContext


@pytest.mark.asyncio
@pytest.mark.unit
async def test_plugin_synthesis_archetype_mode() -> None:
    """Test synthesizing a plugin from an archetype template."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_synth_plugin"
        engine = PluginSynthesisEngine()

        req = SynthesisRequest(
            name="test_synth_plugin",
            mode=SynthesisMode.ARCHETYPE,
            target_dir=str(target),
            description="Synthesized test plugin",
            preset="general",
            tools=["execute_action"],
            auto_validate=True,
        )

        res: SynthesisResult = await engine.synthesize(req)
        assert res.status == "ok"
        assert res.name == "test-synth-plugin"
        assert Path(res.path).exists()
        assert len(res.generated_files) > 0
        assert (target / "plugin.json").exists()
        assert (target / "main.py").exists()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_plugin_synthesis_skill_mode() -> None:
    """Test synthesizing an agent skill with SKILL.md and CARD.md specifications."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_synth_skill"
        engine = PluginSynthesisEngine()

        req = SynthesisRequest(
            name="test_synth_skill",
            mode=SynthesisMode.SKILL,
            target_dir=str(target),
            description="Synthesized test skill",
            category="engineering / meta-skills",
            triggers=["test skill trigger"],
            auto_validate=True,
        )

        res: SynthesisResult = await engine.synthesize(req)
        assert res.status == "ok"
        assert res.name == "test-synth-skill"
        assert (target / "SKILL.md").exists()
        assert (target / "CARD.md").exists()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_plugin_synthesis_dynamic_mode() -> None:
    """Test synthesizing an in-memory dynamic plugin exported to disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_dyn_plugin"
        engine = PluginSynthesisEngine()

        code = '''
def add_numbers(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
'''
        req = SynthesisRequest(
            name="test_dyn_plugin",
            mode=SynthesisMode.DYNAMIC,
            target_dir=str(target),
            code=code,
            auto_validate=True,
        )

        res: SynthesisResult = await engine.synthesize(req)
        assert res.status == "ok"
        assert (target / "plugin.json").exists()
        assert (target / "main.py").exists()


@pytest.mark.unit
def test_plugin_synthesis_list_archetypes() -> None:
    """Test listing archetypes through PluginSynthesisEngine."""
    engine = PluginSynthesisEngine()
    archetypes = engine.list_archetypes()
    assert len(archetypes) > 0
    names = {a["name"] for a in archetypes}
    assert "general" in names
    assert "agentic_workflow" in names


@pytest.mark.asyncio
@pytest.mark.unit
async def test_creator_plugin_ioc_registration() -> None:
    """Test CreatorPlugin registers CREATOR_SERVICE_KEY into ServiceContext."""
    plugin = CreatorPlugin()
    assert CREATOR_SERVICE_KEY in plugin.provides

    ctx = ServiceContext()
    await plugin.on_load(ctx)

    creator_svc = ctx.require(CREATOR_SERVICE_KEY)
    assert creator_svc is not None
    assert hasattr(creator_svc, "synthesize")
    assert hasattr(creator_svc, "validate")
