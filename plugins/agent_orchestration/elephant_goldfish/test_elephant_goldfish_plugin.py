"""Contract test suite for Elephant-Goldfish Plugin."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

# Ensure plugin directory is on sys.path
_PLUGIN_DIR = Path(__file__).parent
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.elephant_goldfish import (
    ELEPHANT_GOLDFISH_SERVICE_KEY,
    ElephantGoldfishService,
)
from plugins.agent_orchestration.elephant_goldfish.main import (
    ElephantGoldfishPlugin,
    egm_detect_drift,
    egm_extract_boundaries,
    egm_review_spec,
    plugin,
)


@pytest.mark.unit
class TestElephantGoldfishPlugin:
    """Validate Elephant-Goldfish Plugin lifecycle, IoC registration, and service protocol."""

    @pytest.mark.asyncio
    async def test_plugin_validator_compliance(self) -> None:
        """Verify plugin passes PluginValidator checks adhering to Rule 34 and Rule 38."""
        report = await PluginValidator.validate(_PLUGIN_DIR)
        assert report.valid is True, f"Plugin validation failed: {report.errors}"

    def test_plugin_metadata_and_singleton(self) -> None:
        """Verify plugin metadata, provides key, and singleton export per Rule 45."""
        assert plugin.name == "plugin.elephant_goldfish"
        assert plugin.version == "1.0.0"
        assert ELEPHANT_GOLDFISH_SERVICE_KEY in plugin.provides
        assert isinstance(plugin, ElephantGoldfishPlugin)
        assert isinstance(plugin, ElephantGoldfishService)

    @pytest.mark.asyncio
    async def test_ioc_context_provision_and_resolution(self) -> None:
        """Verify plugin registers into ServiceContext and resolves via ELEPHANT_GOLDFISH_SERVICE_KEY."""
        ctx = ServiceContext()
        await plugin.on_load(ctx)

        resolved = ctx.require(ELEPHANT_GOLDFISH_SERVICE_KEY)
        assert resolved is plugin

    def test_extract_boundaries_tool(self) -> None:
        """Verify egm_extract_boundaries tool identifies FeatureRange vs DetailedRange."""
        markdown_text = """# Feature X

## Overview
High-altitude architecture overview.

## Implementation Details
Step 1: Write code in src/main.py.
"""
        res = egm_extract_boundaries(markdown_text)
        assert res["has_boundaries"] is True
        assert res["feature_range_start"] == 1
        assert res["detailed_range_start"] > 1

    def test_detect_drift_tool(self) -> None:
        """Verify egm_detect_drift tool evaluates symbol presence in codebase."""
        spec_text = "The system defines `NonExistentSymbol12345` for webhook dispatch."
        workspace_root = Path(__file__).resolve().parents[3]
        res = egm_detect_drift(spec_text, str(workspace_root / "src"))
        assert res["has_drift"] is True
        assert len(res["divergences"]) >= 1
        assert res["divergences"][0]["symbol_name"] == "NonExistentSymbol12345"
