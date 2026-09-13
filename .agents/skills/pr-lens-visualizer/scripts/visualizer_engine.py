"""PR Lens Visualizer domain engine.

Provides slotted, frozen graph models, schema validation, idempotent overlay patching,
standalone animated SVG rendering with inline CSS keyframes, and PR comment composition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import html
from pathlib import Path
import re
from typing import Any


@dataclass(slots=True, frozen=True)
class GraphNode:
    """Immutable graph node representation."""

    id: str
    label: str
    lane: str | None = None
    node_type: str = "service"
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("GraphNode.id cannot be empty")
        if not self.label or not self.label.strip():
            raise ValueError("GraphNode.label cannot be empty")


@dataclass(slots=True, frozen=True)
class GraphEdge:
    """Immutable graph edge representation."""

    source: str
    target: str
    label: str = ""
    animated: bool = True
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.source or not self.source.strip():
            raise ValueError("GraphEdge.source cannot be empty")
        if not self.target or not self.target.strip():
            raise ValueError("GraphEdge.target cannot be empty")


@dataclass(slots=True, frozen=True)
class GraphLane:
    """Immutable architectural lane boundary."""

    id: str
    label: str
    order: int = 0

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("GraphLane.id cannot be empty")
        if not self.label or not self.label.strip():
            raise ValueError("GraphLane.label cannot be empty")


@dataclass(slots=True, frozen=True)
class WalkthroughStep:
    """Immutable progressive disclosure walkthrough step."""

    step: int
    title: str
    description: str
    focus_nodes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.step < 1:
            raise ValueError("WalkthroughStep.step must be >= 1")
        if not self.title or not self.title.strip():
            raise ValueError("WalkthroughStep.title cannot be empty")


@dataclass(slots=True, frozen=True)
class ValidationIssue:
    """Immutable validation issue report."""

    severity: str  # "error" | "warning"
    message: str
    entity_id: str | None = None

    def __post_init__(self) -> None:
        if self.severity not in ("error", "warning"):
            raise ValueError(f"Invalid severity: {self.severity}")
        if not self.message:
            raise ValueError("ValidationIssue.message cannot be empty")


@dataclass(slots=True, frozen=True)
class ValidationResult:
    """Immutable validation report for a graph document."""

    valid: bool
    issues: tuple[ValidationIssue, ...] = field(default_factory=tuple)

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity == "error")

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity == "warning")


@dataclass(slots=True, frozen=True)
class RenderConfig:
    """Configuration for standalone SVG rendering."""

    width: int = 800
    height: int = 600
    theme: str = "auto"
    pulse_animation: bool = True
    node_width: int = 140
    node_height: int = 48


@dataclass(slots=True, frozen=True)
class GraphDocument:
    """Immutable graph document entity."""

    version: str
    title: str
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    lanes: tuple[GraphLane, ...] = field(default_factory=tuple)
    walkthrough: tuple[WalkthroughStep, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.version or not self.version.strip():
            raise ValueError("GraphDocument.version cannot be empty")
        if not self.title or not self.title.strip():
            raise ValueError("GraphDocument.title cannot be empty")


class PrLensVisualizerEngine:
    """Core domain engine for PR Lens graph validation, overlay, rendering, and comment composition."""

    @staticmethod
    def validate_graph(doc: GraphDocument) -> ValidationResult:
        """Validate structural and semantic integrity of a GraphDocument."""
        issues: list[ValidationIssue] = []

        # Check unique node IDs
        seen_nodes: set[str] = set()
        for node in doc.nodes:
            if node.id in seen_nodes:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        message=f"Duplicate node id '{node.id}' detected",
                        entity_id=node.id,
                    )
                )
            seen_nodes.add(node.id)

        # Check unique lane IDs
        lane_ids: set[str] = set()
        for lane in doc.lanes:
            if lane.id in lane_ids:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        message=f"Duplicate lane id '{lane.id}' detected",
                        entity_id=lane.id,
                    )
                )
            lane_ids.add(lane.id)

        # Check node lane membership
        for node in doc.nodes:
            if node.lane is not None and node.lane not in lane_ids:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        message=f"Node '{node.id}' references unknown lane '{node.lane}'",
                        entity_id=node.id,
                    )
                )

        # Check edge endpoints exist
        for edge in doc.edges:
            if edge.source not in seen_nodes:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        message=f"Edge source '{edge.source}' does not exist in nodes",
                        entity_id=edge.source,
                    )
                )
            if edge.target not in seen_nodes:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        message=f"Edge target '{edge.target}' does not exist in nodes",
                        entity_id=edge.target,
                    )
                )

        # Check walkthrough step focus nodes
        for step in doc.walkthrough:
            for fn in step.focus_nodes:
                if fn not in seen_nodes:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            message=f"Walkthrough step {step.step} references unknown focus node '{fn}'",
                            entity_id=fn,
                        )
                    )

        has_errors = any(i.severity == "error" for i in issues)
        return ValidationResult(valid=not has_errors, issues=tuple(issues))

    @staticmethod
    def apply_overlay(doc: GraphDocument, overlay: dict[str, Any]) -> GraphDocument:
        """Apply human-curated map overlay idempotently to a GraphDocument."""
        overlay_lanes_data = overlay.get("lanes") or []
        overlay_nodes_data = overlay.get("nodes") or {}

        # Merge lanes: keep existing, add new from overlay
        existing_lane_map = {lane.id: lane for lane in doc.lanes}
        for ol in overlay_lanes_data:
            lid = ol.get("id")
            llabel = ol.get("label", lid)
            lorder = ol.get("order", len(existing_lane_map))
            if lid:
                existing_lane_map[lid] = GraphLane(id=lid, label=llabel, order=lorder)

        sorted_lanes = tuple(sorted(existing_lane_map.values(), key=lambda l: l.order))

        # Merge nodes
        updated_nodes: list[GraphNode] = []
        for node in doc.nodes:
            if node.id in overlay_nodes_data:
                ov = overlay_nodes_data[node.id]
                new_label = ov.get("label") or node.label
                new_lane = ov.get("lane") or node.lane
                new_type = ov.get("node_type") or node.node_type
                updated_nodes.append(
                    GraphNode(
                        id=node.id,
                        label=new_label,
                        lane=new_lane,
                        node_type=new_type,
                        metadata=node.metadata,
                    )
                )
            else:
                updated_nodes.append(node)

        return GraphDocument(
            version=doc.version,
            title=doc.title,
            nodes=tuple(updated_nodes),
            edges=doc.edges,
            lanes=sorted_lanes,
            walkthrough=doc.walkthrough,
        )

    @staticmethod
    def render_standalone_svg(doc: GraphDocument, config: RenderConfig | None = None) -> str:
        """Render a GraphDocument into a zero-dependency standalone animated SVG."""
        cfg = config or RenderConfig()

        # Simple deterministic layout: arrange nodes by lanes or linear grid
        node_positions: dict[str, tuple[int, int]] = {}
        lanes_list = list(doc.lanes) if doc.lanes else [GraphLane(id="default", label="System", order=0)]
        lane_ids = [l.id for l in lanes_list]

        nodes_per_lane: dict[str, list[GraphNode]] = {lid: [] for lid in lane_ids}
        for node in doc.nodes:
            lid = node.lane if (node.lane and node.lane in nodes_per_lane) else lane_ids[0]
            nodes_per_lane[lid].append(node)

        lane_width = max(cfg.width // max(len(lanes_list), 1), 200)
        lane_margin = 20
        start_y = 70

        svg_lanes_parts: list[str] = []
        for idx, lane in enumerate(lanes_list):
            lx = idx * lane_width + lane_margin
            ly = start_y
            lw = lane_width - (2 * lane_margin)
            lh = cfg.height - start_y - 30

            svg_lanes_parts.append(
                f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" rx="8" class="lane-box" />'
            )
            svg_lanes_parts.append(
                f'<text x="{lx + 12}" y="{ly + 24}" class="lane-label">{html.escape(lane.label)}</text>'
            )

            # Position nodes vertically within lane
            lane_nodes = nodes_per_lane.get(lane.id, [])
            for n_idx, node in enumerate(lane_nodes):
                nx = lx + (lw - cfg.node_width) // 2
                ny = ly + 40 + (n_idx * (cfg.node_height + 25))
                node_positions[node.id] = (nx, ny)

        # Build node SVG elements
        svg_nodes_parts: list[str] = []
        for node in doc.nodes:
            nx, ny = node_positions.get(node.id, (50, 100))
            svg_nodes_parts.append(
                f'<g id="node-{html.escape(node.id)}" class="graph-node">'
                f'<rect x="{nx}" y="{ny}" width="{cfg.node_width}" height="{cfg.node_height}" rx="6" class="node-rect" />'
                f'<text x="{nx + cfg.node_width // 2}" y="{ny + cfg.node_height // 2 + 5}" class="node-label">'
                f'{html.escape(node.label)}</text></g>'
            )

        # Build edge SVG paths
        svg_edges_parts: list[str] = []
        for edge in doc.edges:
            sp = node_positions.get(edge.source)
            tp = node_positions.get(edge.target)
            if not sp or not tp:
                continue

            x1 = sp[0] + cfg.node_width
            y1 = sp[1] + cfg.node_height // 2
            x2 = tp[0]
            y2 = tp[1] + cfg.node_height // 2

            # Smooth cubic curve
            dx = max((x2 - x1) // 2, 30)
            d_path = f"M {x1} {y1} C {x1 + dx} {y1}, {x2 - dx} {y2}, {x2} {y2}"
            anim_class = "edge-path animated-pulse" if (cfg.pulse_animation and edge.animated) else "edge-path"

            svg_edges_parts.append(
                f'<path d="{d_path}" class="{anim_class}" marker-end="url(#arrow)" />'
            )
            if edge.label:
                mx = (x1 + x2) // 2
                my = (y1 + y2) // 2 - 8
                svg_edges_parts.append(
                    f'<text x="{mx}" y="{my}" class="edge-label">{html.escape(edge.label)}</text>'
                )

        style_content = """
    :root {
      --bg-color: #ffffff;
      --lane-bg: #f6f8fa;
      --lane-stroke: #d0d7de;
      --lane-text: #57606a;
      --node-bg: #ffffff;
      --node-stroke: #0969da;
      --node-text: #24292f;
      --edge-stroke: #0969da;
      --edge-label: #57606a;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg-color: #0d1117;
        --lane-bg: #161b22;
        --lane-stroke: #30363d;
        --lane-text: #8b949e;
        --node-bg: #21262d;
        --node-stroke: #58a6ff;
        --node-text: #c9d1d9;
        --edge-stroke: #58a6ff;
        --edge-label: #8b949e;
      }
    }
    .bg { fill: var(--bg-color); }
    .lane-box { fill: var(--lane-bg); stroke: var(--lane-stroke); stroke-width: 1px; }
    .lane-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 13px; font-weight: 600; fill: var(--lane-text); }
    .node-rect { fill: var(--node-bg); stroke: var(--node-stroke); stroke-width: 2px; }
    .node-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 12px; font-weight: 500; fill: var(--node-text); text-anchor: middle; }
    .edge-path { fill: none; stroke: var(--edge-stroke); stroke-width: 2px; }
    .edge-label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 11px; fill: var(--edge-label); text-anchor: middle; }
    .title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 18px; font-weight: 700; fill: var(--node-text); }
    .animated-pulse {
      stroke-dasharray: 8, 4;
      animation: pulse-flow 1.5s linear infinite;
    }
    @keyframes pulse-flow {
      to {
        stroke-dashoffset: -24;
      }
    }
"""

        svg_output = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cfg.width} {cfg.height}" width="100%" height="100%" class="pr-lens-svg">
  <defs>
    <style>{style_content}    </style>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="var(--edge-stroke)" />
    </marker>
  </defs>
  <rect width="{cfg.width}" height="{cfg.height}" class="bg" rx="10" />
  <text x="24" y="38" class="title">{html.escape(doc.title)}</text>
  <g class="lanes-layer">
    {"".join(svg_lanes_parts)}
  </g>
  <g class="edges-layer">
    {"".join(svg_edges_parts)}
  </g>
  <g class="nodes-layer">
    {"".join(svg_nodes_parts)}
  </g>
</svg>"""
        return svg_output

    @staticmethod
    def compose_pr_comment(
        doc: GraphDocument,
        svg_content: str,
        summary: str,
    ) -> str:
        """Compose GitHub PR markdown comment containing diagram and progressive disclosure walkthrough."""
        walkthrough_md: list[str] = []
        if doc.walkthrough:
            walkthrough_md.append("### Progressive Walkthrough (ELI5)")
            for step in doc.walkthrough:
                focus_str = f" `[{', '.join(step.focus_nodes)}]`" if step.focus_nodes else ""
                walkthrough_md.append(
                    f"**Step {step.step}: {step.title}**{focus_str}\n{step.description}\n"
                )

        walkthrough_text = "\n".join(walkthrough_md) if walkthrough_md else ""

        comment = f"""## PR Architecture & Data-Flow Visualizer

{summary}

<details open>
<summary><b>Architecture Diagram (Animated SVG)</b></summary>

{svg_content}

</details>

{walkthrough_text}

---
*Generated by PR Lens Visualizer (zero external dependencies, standalone SVG).*
"""
        return comment

    @staticmethod
    def parse_git_diff(diff_text: str) -> GraphDocument:
        """Parse unified git diff into an initial GraphDocument topology."""
        file_pattern = re.compile(r"^diff --git a/(.*?) b/(.*?)$", re.MULTILINE)
        matches = file_pattern.findall(diff_text)

        nodes: list[GraphNode] = []
        lanes: list[GraphLane] = [
            GraphLane(id="frontend", label="Frontend / UI", order=1),
            GraphLane(id="kernel", label="Core Kernel", order=2),
            GraphLane(id="services", label="Services & Plugins", order=3),
            GraphLane(id="storage", label="Storage & Data", order=4),
        ]
        edges: list[GraphEdge] = []

        seen_files: set[str] = set()
        for _, b_path in matches:
            if b_path in seen_files:
                continue
            seen_files.add(b_path)

            # Determine lane from path
            lane = "services"
            if "kernel" in b_path:
                lane = "kernel"
            elif "ui" in b_path or "web" in b_path:
                lane = "frontend"
            elif "storage" in b_path or "db" in b_path:
                lane = "storage"

            node_id = b_path.replace("/", "_").replace(".", "_")
            nodes.append(
                GraphNode(
                    id=node_id,
                    label=Path(b_path).name,
                    lane=lane,
                    node_type="file",
                )
            )

        # Connect sequential nodes if multiple
        for i in range(len(nodes) - 1):
            edges.append(
                GraphEdge(
                    source=nodes[i].id,
                    target=nodes[i + 1].id,
                    label="flows to",
                    animated=True,
                )
            )

        return GraphDocument(
            version="1.0.0",
            title="PR Architecture Delta",
            nodes=tuple(nodes),
            edges=tuple(edges),
            lanes=tuple(lanes),
        )
