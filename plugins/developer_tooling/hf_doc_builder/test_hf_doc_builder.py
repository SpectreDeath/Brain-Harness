"""Unit tests and validator compliance for hf_doc_builder plugin (Rule 34, 38, 45)."""

from __future__ import annotations

from pathlib import Path
import sys
import pytest

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.doc_builder import DOC_BUILDER_SERVICE_KEY

_PLUGIN_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_PLUGIN_DIR))

from main import (
    HfDocBuilderPlugin,
    doc_autodoc_inspect,
    doc_chunk_indexer,
    doc_format_convert,
    doc_link_verify,
    doc_style_lint,
    plugin,
)


@pytest.mark.unit
def test_plugin_validator_compliance() -> None:
    """Rule 34 & Rule 38: Verify plugin passes PluginValidator using validate_sync."""
    report = PluginValidator.validate_sync(_PLUGIN_DIR)
    assert report.valid, f"Plugin validation failed: {[c.message for c in report.checks if not c.passed]}"
    assert len(report.checks) > 0


@pytest.mark.unit
def test_plugin_module_singleton() -> None:
    """Rule 45: Verify plugin exports instantiated singleton and declares provides."""
    assert plugin is not None
    assert isinstance(plugin, HfDocBuilderPlugin)
    assert DOC_BUILDER_SERVICE_KEY in plugin.provides
    assert plugin.name == "plugin.hf_doc_builder"
    assert plugin.version == "1.0.0"


@pytest.mark.asyncio
async def test_plugin_ioc_lifecycle() -> None:
    """Verify plugin registers into IoC ServiceContext on_load."""
    context = ServiceContext()
    await plugin.on_load(context)

    resolved = context.require(DOC_BUILDER_SERVICE_KEY)
    assert resolved is plugin


@pytest.mark.unit
def test_plugin_tool_entrypoints() -> None:
    """Verify tool entrypoint functions execute and return valid serializable dictionaries."""
    # 1. doc_autodoc_inspect
    res_inspect = doc_autodoc_inspect(package_name="json", object_name="dumps")
    assert "dumps" in res_inspect["object_path"]
    assert "parameters" in res_inspect

    # 2. doc_format_convert
    res_convert = doc_format_convert(source_path="# Test\n\n> [!NOTE]\nNote text.\n")
    assert "<Tip>" in res_convert["converted_content"]
    assert "<Tip>" in res_convert["svelte_components_injected"]

    # 3. doc_chunk_indexer
    chunks = doc_chunk_indexer(markdown_text="# H1\n\nBody text\n\n## H2\n\nSub section")
    assert len(chunks) == 2
    assert chunks[0]["title"] == "H1"
    assert chunks[1]["title"] == "H2"
