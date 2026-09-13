"""Test suite for pr-lens-visualizer skill engine adhering to Rule 12 and Rule 43."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure skill scripts directory is importable
skill_scripts = Path(__file__).parent.parent / ".agents" / "skills" / "pr-lens-visualizer" / "scripts"
if str(skill_scripts) not in sys.path:
    sys.path.insert(0, str(skill_scripts))

from visualizer_engine import (  # type: ignore
    GraphDocument,
    GraphEdge,
    GraphLane,
    GraphNode,
    PrLensVisualizerEngine,
    WalkthroughStep,
)


@pytest.mark.unit
class TestPrLensVisualizerEngine:
    """Validate domain engine, immutability, integrity validation, and SVG generation."""

    def test_slotted_frozen_dataclasses_immutability(self) -> None:
        """Verify slotted/frozen dataclass immutability using direct assignment per Rule 43."""
        node = GraphNode(id="n1", label="Node 1", lane="core")
        edge = GraphEdge(source="n1", target="n2", label="links")
        lane = GraphLane(id="core", label="Core Engine")
        step = WalkthroughStep(step=1, title="Intro", description="Starting point")

        # Direct attribute assignment must raise AttributeError/TypeError (Rule 43)
        with pytest.raises((AttributeError, TypeError)):
            node.label = "mutated"  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            edge.label = "mutated"  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            lane.label = "mutated"  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            step.title = "mutated"  # type: ignore

    def test_graph_validation_valid_document(self) -> None:
        """Verify valid GraphDocument passes integrity checks."""
        nodes = (
            GraphNode(id="client", label="Client UI", lane="ui"),
            GraphNode(id="server", label="API Server", lane="backend"),
        )
        lanes = (
            GraphLane(id="ui", label="User Interface"),
            GraphLane(id="backend", label="Backend Services"),
        )
        edges = (
            GraphEdge(source="client", target="server", label="HTTP POST", animated=True),
        )
        walkthrough = (
            WalkthroughStep(step=1, title="Request Dispatch", description="Client calls server", focus_nodes=("client", "server")),
        )
        doc = GraphDocument(
            version="1.0.0",
            title="Sample Flow",
            nodes=nodes,
            edges=edges,
            lanes=lanes,
            walkthrough=walkthrough,
        )

        result = PrLensVisualizerEngine.validate_graph(doc)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_graph_validation_integrity_violations(self) -> None:
        """Verify dangling edge, unknown lane, and unknown focus node errors."""
        nodes = (
            GraphNode(id="n1", label="Node 1", lane="unknown_lane"),
        )
        edges = (
            GraphEdge(source="n1", target="dangling_target", label="bad edge"),
        )
        walkthrough = (
            WalkthroughStep(step=1, title="Step 1", description="Invalid step", focus_nodes=("dangling_node",)),
        )
        doc = GraphDocument(
            version="1.0.0",
            title="Defective Flow",
            nodes=nodes,
            edges=edges,
            lanes=(),
            walkthrough=walkthrough,
        )

        result = PrLensVisualizerEngine.validate_graph(doc)
        assert result.valid is False
        error_msgs = [e.message for e in result.errors]
        assert any("unknown lane" in msg for msg in error_msgs)
        assert any("does not exist in nodes" in msg for msg in error_msgs)
        assert any("references unknown focus node" in msg for msg in error_msgs)

    def test_idempotent_overlay_application(self) -> None:
        """Verify overlay updates labels and lanes idempotently without clobbering nodes."""
        nodes = (
            GraphNode(id="n1", label="Raw Node 1", lane=None),
            GraphNode(id="n2", label="Raw Node 2", lane=None),
        )
        doc = GraphDocument(
            version="1.0.0",
            title="Raw Graph",
            nodes=nodes,
            edges=(),
        )

        overlay = {
            "lanes": [
                {"id": "curated_lane", "label": "Curated Domain", "order": 1}
            ],
            "nodes": {
                "n1": {"label": "Curated Node 1", "lane": "curated_lane"}
            }
        }

        patched = PrLensVisualizerEngine.apply_overlay(doc, overlay)
        assert len(patched.nodes) == 2
        assert patched.nodes[0].label == "Curated Node 1"
        assert patched.nodes[0].lane == "curated_lane"
        assert patched.nodes[1].label == "Raw Node 2"
        assert len(patched.lanes) == 1
        assert patched.lanes[0].id == "curated_lane"

    def test_render_standalone_svg_contains_inline_keyframes(self) -> None:
        """Verify generated SVG is self-contained with inline CSS @keyframes and dark mode."""
        nodes = (
            GraphNode(id="ui", label="Web App", lane="frontend"),
            GraphNode(id="api", label="GraphQL API", lane="backend"),
        )
        lanes = (
            GraphLane(id="frontend", label="Frontend", order=1),
            GraphLane(id="backend", label="Backend", order=2),
        )
        edges = (
            GraphEdge(source="ui", target="api", label="GraphQL Query", animated=True),
        )
        doc = GraphDocument(
            version="1.0.0",
            title="Architecture Overview",
            nodes=nodes,
            edges=edges,
            lanes=lanes,
        )

        svg = PrLensVisualizerEngine.render_standalone_svg(doc)
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert "@keyframes pulse-flow" in svg
        assert "prefers-color-scheme: dark" in svg
        assert "Web App" in svg
        assert "GraphQL API" in svg
        assert "animated-pulse" in svg

    def test_compose_pr_comment_contains_diagram_and_walkthrough(self) -> None:
        """Verify PR comment markdown composition."""
        nodes = (GraphNode(id="n1", label="Node 1"),)
        step = WalkthroughStep(step=1, title="Start Here", description="Initial node activation", focus_nodes=("n1",))
        doc = GraphDocument(
            version="1.0.0",
            title="PR Comment Test",
            nodes=nodes,
            edges=(),
            walkthrough=(step,),
        )

        svg = "<svg>mock</svg>"
        comment = PrLensVisualizerEngine.compose_pr_comment(doc, svg, "Changes summary")
        assert "## PR Architecture & Data-Flow Visualizer" in comment
        assert "Changes summary" in comment
        assert "<svg>mock</svg>" in comment
        assert "Progressive Walkthrough (ELI5)" in comment
        assert "Step 1: Start Here" in comment

    def test_parse_git_diff(self) -> None:
        """Verify git diff text parsing extracts nodes, lanes, and edges."""
        diff_text = """diff --git a/src/kernel/context.py b/src/kernel/context.py
index 123..456 100644
--- a/src/kernel/context.py
+++ b/src/kernel/context.py
@@ -1,3 +1,4 @@
+new code
diff --git a/src/ui/dashboard.py b/src/ui/dashboard.py
index 789..abc 100644
--- a/src/ui/dashboard.py
+++ b/src/ui/dashboard.py
@@ -1,3 +1,4 @@
+dashboard update
"""
        doc = PrLensVisualizerEngine.parse_git_diff(diff_text)
        assert len(doc.nodes) == 2
        assert any(n.label == "context.py" and n.lane == "kernel" for n in doc.nodes)
        assert any(n.label == "dashboard.py" and n.lane == "frontend" for n in doc.nodes)
        assert len(doc.edges) == 1
