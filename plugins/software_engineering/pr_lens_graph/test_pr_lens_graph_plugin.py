"""Contract test suite for PR Lens Graph Plugin."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure plugin directory is on sys.path
_PLUGIN_DIR = Path(__file__).parent
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.pr_lens import (
    PR_LENS_GRAPH_SERVICE_KEY,
    PrLensGraphService,
)
from plugins.software_engineering.pr_lens_graph.main import (
    PrLensGraphPlugin,
    plugin,
    pr_lens_analyze,
    pr_lens_comment,
    pr_lens_diff,
    pr_lens_render,
    pr_lens_validate,
)


@pytest.mark.unit
class TestPrLensGraphPlugin:
    """Validate PR Lens Graph Plugin lifecycle, IoC registration, and service protocol."""

    def test_plugin_validator_compliance(self) -> None:
        """Verify plugin passes PluginValidator checks adhering to Rule 34 and Rule 38."""
        report = PluginValidator.validate_sync(_PLUGIN_DIR)
        assert report.valid is True, f"Plugin validation failed: {report.errors}"

    def test_plugin_metadata_and_singleton(self) -> None:
        """Verify plugin metadata, provides key, and singleton export per Rule 45."""
        assert plugin.name == "plugin.pr_lens_graph"
        assert plugin.version == "1.0.0"
        assert PR_LENS_GRAPH_SERVICE_KEY in plugin.provides
        assert isinstance(plugin, PrLensGraphPlugin)
        assert isinstance(plugin, PrLensGraphService)

    @pytest.mark.asyncio
    async def test_ioc_context_provision_and_resolution(self) -> None:
        """Verify plugin registers into ServiceContext and resolves via PR_LENS_GRAPH_SERVICE_KEY."""
        ctx = ServiceContext()
        await plugin.on_load(ctx)

        resolved = ctx.require(PR_LENS_GRAPH_SERVICE_KEY)
        assert resolved is plugin

    def test_pr_lens_validate_tool(self) -> None:
        """Verify pr_lens_validate detects valid documents and flags integrity errors."""
        valid_doc = {
            "version": "1.0.0",
            "title": "Auth Flow",
            "nodes": [
                {"id": "ui", "label": "Login Page", "lane": "client"},
                {"id": "api", "label": "OAuth API", "lane": "server"},
            ],
            "lanes": [
                {"id": "client", "label": "Client Side"},
                {"id": "server", "label": "Server Side"},
            ],
            "edges": [
                {"source": "ui", "target": "api", "label": "POST /auth"},
            ],
        }
        res_valid = plugin.validate(valid_doc)
        assert res_valid.valid is True
        assert res_valid.errors_count == 0

        # Invalid doc with dangling edge and unknown lane
        invalid_doc = {
            "version": "1.0.0",
            "title": "Broken Flow",
            "nodes": [
                {"id": "ui", "label": "Login Page", "lane": "nonexistent_lane"},
            ],
            "lanes": [],
            "edges": [
                {"source": "ui", "target": "missing_node", "label": "broken"},
            ],
        }
        res_invalid = plugin.validate(invalid_doc)
        assert res_invalid.valid is False
        assert res_invalid.errors_count >= 2

    def test_pr_lens_render_tool(self) -> None:
        """Verify pr_lens_render compiles standalone animated SVG."""
        doc = {
            "version": "1.0.0",
            "title": "Rendering Test",
            "nodes": [{"id": "n1", "label": "Node 1"}],
            "edges": [],
        }
        res = plugin.render(doc, {"width": 800, "height": 500, "theme": "dark"})
        assert res.node_count == 1
        assert res.theme == "dark"
        assert res.svg_content.startswith("<svg")
        assert res.svg_content.endswith("</svg>")
        assert "@keyframes pulse-flow" in res.svg_content

    def test_pr_lens_analyze_and_overlay_tool(self) -> None:
        """Verify pr_lens_analyze parses diff text and applies architectural overlay."""
        diff_text = """diff --git a/src/kernel/bus.py b/src/kernel/bus.py
index 111..222 100644
--- a/src/kernel/bus.py
+++ b/src/kernel/bus.py
@@ -1,2 +1,3 @@
+event bus
"""
        overlay = {
            "lanes": [{"id": "core_kernel", "label": "Kernel Core", "order": 1}],
            "nodes": {"src_kernel_bus_py": {"label": "EventBus", "lane": "core_kernel"}},
        }
        res = plugin.analyze(diff_text, overlay)
        assert "Synthesized architecture" in res.summary
        nodes = res.graph_doc.get("nodes", [])
        assert len(nodes) == 1
        assert nodes[0]["label"] == "EventBus"
        assert nodes[0]["lane"] == "core_kernel"

    def test_pr_lens_diff_tool_safe_execution(self) -> None:
        """Verify pr_lens_diff executes without crashing and adheres to Rule 14 pipe cleanup."""
        # Test diff extraction on current repo
        diff_res = plugin.diff(base_ref="HEAD", head_ref="HEAD")
        assert isinstance(diff_res.diff_text, str)
        assert isinstance(diff_res.files_changed, list)

    def test_pr_lens_comment_tool(self) -> None:
        """Verify pr_lens_comment produces formatted markdown PR comment."""
        analysis = {
            "summary": "Diff analysis",
            "graph_doc": {
                "version": "1.0.0",
                "title": "PR Flow",
                "nodes": [{"id": "a", "label": "Alpha"}],
                "edges": [],
                "walkthrough": [
                    {"step": 1, "title": "Alpha Phase", "description": "Initialization", "focus_nodes": ["a"]}
                ],
            },
        }
        svg = "<svg>mock svg</svg>"
        comment_res = plugin.comment(analysis, svg)
        assert "PR Architecture & Data-Flow Visualizer" in comment_res.markdown_comment
        assert "<svg>mock svg</svg>" in comment_res.markdown_comment
        assert "Step 1: Alpha Phase" in comment_res.markdown_comment
        assert comment_res.has_diagram is True
        assert comment_res.has_walkthrough is True

    def test_top_level_entrypoint_functions(self) -> None:
        """Verify top-level function wrappers declared in manifest function properly."""
        val_res = pr_lens_validate({"version": "1.0.0", "title": "T", "nodes": [{"id": "n1", "label": "L"}]})
        assert val_res["valid"] is True

        render_res = pr_lens_render({"version": "1.0.0", "title": "T", "nodes": [{"id": "n1", "label": "L"}]})
        assert "<svg" in render_res["svg_content"]

        diff_res = pr_lens_diff(base_ref="HEAD", head_ref="HEAD")
        assert "diff_text" in diff_res

        an_res = pr_lens_analyze("diff --git a/x.py b/x.py\n+hello\n")
        assert "graph_doc" in an_res

        comment_res = pr_lens_comment(an_res, "<svg></svg>")
        assert "markdown_comment" in comment_res

