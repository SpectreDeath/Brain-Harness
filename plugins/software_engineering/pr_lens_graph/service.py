"""PR Lens Graph Service implementation."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import structlog

# Add skill scripts directory to sys.path to resolve visualizer engine
_SKILL_SCRIPTS = Path(__file__).resolve().parents[3] / ".agents" / "skills" / "pr-lens-visualizer" / "scripts"
if _SKILL_SCRIPTS.exists() and str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from visualizer_engine import (  # type: ignore
    GraphDocument,
    GraphEdge,
    GraphLane,
    GraphNode,
    PrLensVisualizerEngine,
    RenderConfig,
    WalkthroughStep,
)

from harness.services.pr_lens import (
    PrLensAnalysisData,
    PrLensCommentData,
    PrLensDiffData,
    PrLensGraphService,
    PrLensRenderData,
    PrLensValidationData,
)

logger = structlog.get_logger(__name__)


def dict_to_graph_doc(data: dict[str, Any]) -> GraphDocument:
    """Convert raw dictionary into slotted/frozen GraphDocument entity."""
    raw_nodes = data.get("nodes") or []
    raw_edges = data.get("edges") or []
    raw_lanes = data.get("lanes") or []
    raw_wt = data.get("walkthrough") or []

    nodes: list[GraphNode] = []
    for n in raw_nodes:
        if isinstance(n, dict):
            nodes.append(
                GraphNode(
                    id=n.get("id", ""),
                    label=n.get("label", n.get("id", "")),
                    lane=n.get("lane"),
                    node_type=n.get("node_type", "service"),
                )
            )

    edges: list[GraphEdge] = []
    for e in raw_edges:
        if isinstance(e, dict):
            edges.append(
                GraphEdge(
                    source=e.get("source", ""),
                    target=e.get("target", ""),
                    label=e.get("label", ""),
                    animated=e.get("animated", True),
                )
            )

    lanes: list[GraphLane] = []
    for l in raw_lanes:
        if isinstance(l, dict):
            lanes.append(
                GraphLane(
                    id=l.get("id", ""),
                    label=l.get("label", l.get("id", "")),
                    order=l.get("order", 0),
                )
            )

    walkthrough: list[WalkthroughStep] = []
    for step_idx, w in enumerate(raw_wt, start=1):
        if isinstance(w, dict):
            fn = tuple(w.get("focus_nodes") or ())
            walkthrough.append(
                WalkthroughStep(
                    step=w.get("step", step_idx),
                    title=w.get("title", f"Step {step_idx}"),
                    description=w.get("description", ""),
                    focus_nodes=fn,
                )
            )

    return GraphDocument(
        version=data.get("version", "1.0.0"),
        title=data.get("title", "Architecture Diagram"),
        nodes=tuple(nodes),
        edges=tuple(edges),
        lanes=tuple(lanes),
        walkthrough=tuple(walkthrough),
    )


def graph_doc_to_dict(doc: GraphDocument) -> dict[str, Any]:
    """Convert GraphDocument back to serializable dictionary."""
    return {
        "version": doc.version,
        "title": doc.title,
        "nodes": [
            {"id": n.id, "label": n.label, "lane": n.lane, "node_type": n.node_type}
            for n in doc.nodes
        ],
        "edges": [
            {"source": e.source, "target": e.target, "label": e.label, "animated": e.animated}
            for e in doc.edges
        ],
        "lanes": [
            {"id": l.id, "label": l.label, "order": l.order}
            for l in doc.lanes
        ],
        "walkthrough": [
            {"step": w.step, "title": w.title, "description": w.description, "focus_nodes": list(w.focus_nodes)}
            for w in doc.walkthrough
        ],
    }


class PrLensGraphServiceImpl(PrLensGraphService):
    """Implementation of PrLensGraphService executing engine transformations."""

    def validate(self, graph_doc: dict[str, Any]) -> PrLensValidationData:
        """Validate structural and semantic integrity of a graph document dictionary."""
        try:
            doc = dict_to_graph_doc(graph_doc)
            res = PrLensVisualizerEngine.validate_graph(doc)
            issues_list = [
                {"severity": i.severity, "message": i.message, "entity_id": i.entity_id}
                for i in res.issues
            ]
            return PrLensValidationData(
                valid=res.valid,
                issues=issues_list,
                errors_count=len(res.errors),
                warnings_count=len(res.warnings),
            )
        except Exception as err:
            logger.error("pr_lens_validate_error", error=str(err))
            return PrLensValidationData(
                valid=False,
                issues=[{"severity": "error", "message": f"Malformed graph schema: {err}", "entity_id": None}],
                errors_count=1,
                warnings_count=0,
            )

    def render(
        self,
        graph_doc: dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> PrLensRenderData:
        """Render a graph document into a standalone animated SVG."""
        cfg_dict = config or {}
        doc = dict_to_graph_doc(graph_doc)
        render_cfg = RenderConfig(
            width=cfg_dict.get("width", 800),
            height=cfg_dict.get("height", 600),
            theme=cfg_dict.get("theme", "auto"),
            pulse_animation=cfg_dict.get("pulse_animation", True),
        )
        svg_str = PrLensVisualizerEngine.render_standalone_svg(doc, render_cfg)
        return PrLensRenderData(
            svg_content=svg_str,
            node_count=len(doc.nodes),
            edge_count=len(doc.edges),
            lane_count=len(doc.lanes),
            theme=render_cfg.theme,
        )

    def diff(
        self,
        base_ref: str = "HEAD~1",
        head_ref: str = "HEAD",
        repo_path: str | None = None,
    ) -> PrLensDiffData:
        """Extract unified git diff between two commit references with Rule 14 pipe cleanup."""
        target_cwd = repo_path or os.getcwd()
        cmd = ["git", "diff", f"{base_ref}..{head_ref}"]
        
        proc: subprocess.Popen[str] | None = None
        stdout_data = ""
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=target_cwd,
                encoding="utf-8",
                errors="replace",
            )
            stdout_data, _stderr_data = proc.communicate(timeout=30)
        except Exception as err:
            logger.warning("git_diff_execution_failed", error=str(err))
            stdout_data = ""
        finally:
            # Rule 14: Subprocess Pipe Transport Disposal Invariant
            if proc is not None:
                if proc.stdout and not proc.stdout.closed:
                    try:
                        proc.stdout.close()
                    except Exception:
                        pass
                if proc.stderr and not proc.stderr.closed:
                    try:
                        proc.stderr.close()
                    except Exception:
                        pass

        # Parse touched file paths
        file_pattern = re.compile(r"^diff --git a/(.*?) b/(.*?)$", re.MULTILINE)
        files = [m[1] for m in file_pattern.findall(stdout_data)]

        return PrLensDiffData(
            diff_text=stdout_data,
            files_changed=files,
            stats={"files_count": len(files)},
        )

    def analyze(
        self,
        diff_text: str,
        overlay_map: dict[str, Any] | None = None,
    ) -> PrLensAnalysisData:
        """Synthesize a GraphDocument from diff text and apply optional architectural overlay."""
        doc = PrLensVisualizerEngine.parse_git_diff(diff_text)
        if overlay_map:
            doc = PrLensVisualizerEngine.apply_overlay(doc, overlay_map)

        doc_dict = graph_doc_to_dict(doc)
        wt_list = [
            {"step": w.step, "title": w.title, "description": w.description, "focus_nodes": list(w.focus_nodes)}
            for w in doc.walkthrough
        ]

        summary = f"Synthesized architecture topology across {len(doc.nodes)} nodes and {len(doc.lanes)} lanes."
        return PrLensAnalysisData(
            summary=summary,
            graph_doc=doc_dict,
            walkthrough=wt_list,
        )

    def comment(
        self,
        analysis: dict[str, Any],
        svg_content: str,
    ) -> PrLensCommentData:
        """Compose GitHub PR markdown comment enclosing diagram and progressive walkthrough."""
        raw_doc = analysis.get("graph_doc") if "graph_doc" in analysis else analysis
        doc = dict_to_graph_doc(raw_doc)
        summary = analysis.get("summary", "PR Architectural Diff Analysis")
        md_comment = PrLensVisualizerEngine.compose_pr_comment(doc, svg_content, summary)

        return PrLensCommentData(
            markdown_comment=md_comment,
            has_diagram=bool(svg_content and "<svg" in svg_content),
            has_walkthrough=bool(doc.walkthrough),
        )
