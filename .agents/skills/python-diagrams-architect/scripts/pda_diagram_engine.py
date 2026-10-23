# -*- coding: utf-8 -*-
"""Authoritative Python Diagrams-as-Code Engine.

Implements slotted & frozen dataclass domain models (Rule 12, Rule 43),
code generation, static AST and architectural linting, and canonical presets.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
import sys
from typing import Any

# Ensure UTF-8 streams per Rule 23 and Rule 50
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

VALID_PROVIDERS: frozenset[str] = frozenset({
    "aws",
    "azure",
    "gcp",
    "k8s",
    "onprem",
    "openstack",
    "outscale",
    "saas",
    "generic",
})

VALID_DIRECTIONS: frozenset[str] = frozenset({"LR", "TB", "RL", "BT"})
VALID_FORMATS: frozenset[str] = frozenset({"png", "jpg", "svg", "pdf"})
VALID_EDGE_STYLES: frozenset[str] = frozenset({"solid", "dashed", "dotted", "bold"})
VALID_EDGE_DIRECTIONS: frozenset[str] = frozenset({">>", "<<", "-"})


@dataclass(slots=True, frozen=True)
class DiagramNode:
    """Immutable domain representation of an architectural component node (Rule 12)."""

    provider: str
    resource_type: str
    class_name: str
    label: str
    var_name: str
    cluster_path: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.provider or not self.provider.strip():
            raise ValueError("DiagramNode.provider must be a non-empty string.")
        if not self.resource_type or not self.resource_type.strip():
            raise ValueError("DiagramNode.resource_type must be a non-empty string.")
        if not self.class_name or not self.class_name.strip():
            raise ValueError("DiagramNode.class_name must be a non-empty string.")
        if not self.label or not self.label.strip():
            raise ValueError("DiagramNode.label must be a non-empty string.")
        if not self.var_name or not self.var_name.strip():
            raise ValueError("DiagramNode.var_name must be a non-empty string.")


@dataclass(slots=True, frozen=True)
class DiagramEdge:
    """Immutable domain representation of a directional communication channel (Rule 12)."""

    source: str
    target: str
    direction: str = ">>"
    label: str | None = None
    color: str | None = None
    style: str | None = None

    def __post_init__(self) -> None:
        if not self.source or not self.source.strip():
            raise ValueError("DiagramEdge.source must be non-empty.")
        if not self.target or not self.target.strip():
            raise ValueError("DiagramEdge.target must be non-empty.")
        if self.direction not in VALID_EDGE_DIRECTIONS:
            raise ValueError(
                f"Invalid edge direction '{self.direction}'. Expected one of {sorted(VALID_EDGE_DIRECTIONS)}"
            )
        if self.style is not None and self.style not in VALID_EDGE_STYLES:
            raise ValueError(
                f"Invalid edge style '{self.style}'. Expected one of {sorted(VALID_EDGE_STYLES)}"
            )


@dataclass(slots=True, frozen=True)
class DiagramCluster:
    """Immutable domain representation of an architectural cluster boundary (Rule 12)."""

    name: str
    parent_path: tuple[str, ...] = ()
    direction: str = "LR"

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("DiagramCluster.name must be non-empty.")
        if self.direction not in VALID_DIRECTIONS:
            raise ValueError(
                f"Invalid cluster direction '{self.direction}'. Expected one of {sorted(VALID_DIRECTIONS)}"
            )


@dataclass(slots=True, frozen=True)
class DiagramSpec:
    """Immutable specification container for a complete architecture diagram (Rule 12)."""

    title: str
    filename: str
    direction: str = "LR"
    outformat: str = "png"
    nodes: tuple[DiagramNode, ...] = ()
    clusters: tuple[DiagramCluster, ...] = ()
    edges: tuple[DiagramEdge, ...] = ()
    show: bool = False

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("DiagramSpec.title must be non-empty.")
        if not self.filename or not self.filename.strip():
            raise ValueError("DiagramSpec.filename must be non-empty.")
        if self.direction not in VALID_DIRECTIONS:
            raise ValueError(
                f"Invalid diagram direction '{self.direction}'. Expected one of {sorted(VALID_DIRECTIONS)}"
            )
        if self.outformat not in VALID_FORMATS:
            raise ValueError(
                f"Invalid outformat '{self.outformat}'. Expected one of {sorted(VALID_FORMATS)}"
            )


@dataclass(slots=True, frozen=True)
class DiagramValidationReport:
    """Immutable diagnostic report detailing validation checks and lint issues (Rule 12, Rule 34)."""

    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    node_count: int
    edge_count: int
    cluster_count: int
    providers_used: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.node_count < 0 or self.edge_count < 0 or self.cluster_count < 0:
            raise ValueError("Counts must be non-negative integers.")


class PythonDiagramsEngine:
    """Authoritative generator, validator, and linting engine for Diagrams-as-Code."""

    @classmethod
    def generate_code(cls, spec: DiagramSpec) -> str:
        """Generate executable, PEP 8 compliant Python diagram code from a DiagramSpec."""
        lines: list[str] = [
            "# -*- coding: utf-8 -*-",
            '"""Autogenerated Architecture Diagram using Python Diagrams-as-Code."""',
            "",
        ]

        # Determine imports
        has_clusters = len(spec.clusters) > 0
        has_custom_edges = any(
            (e.label or e.color or e.style) for e in spec.edges
        )

        diagram_imports = ["Diagram"]
        if has_clusters:
            diagram_imports.append("Cluster")
        if has_custom_edges:
            diagram_imports.append("Edge")

        lines.append(f"from diagrams import {', '.join(diagram_imports)}")

        # Deduplicate node imports: diagrams.<provider>.<resource_type> -> class_name
        import_map: dict[str, set[str]] = {}
        for node in spec.nodes:
            mod_path = f"diagrams.{node.provider.lower()}.{node.resource_type.lower()}"
            import_map.setdefault(mod_path, set()).add(node.class_name)

        for mod_path in sorted(import_map.keys()):
            classes = sorted(import_map[mod_path])
            lines.append(f"from {mod_path} import {', '.join(classes)}")

        lines.append("")
        show_str = "True" if spec.show else "False"
        lines.append(
            f'with Diagram("{spec.title}", filename="{spec.filename}", direction="{spec.direction}", outformat="{spec.outformat}", show={show_str}):'
        )

        # Build cluster hierarchy tree
        # cluster_path: tuple of names
        # Root nodes have empty cluster_path ()
        root_nodes = [n for n in spec.nodes if not n.cluster_path]

        # Group clusters by hierarchy
        # Map cluster name to its DiagramCluster object
        cluster_dict = {c.name: c for c in spec.clusters}

        # Find top-level clusters (parent_path is empty)
        top_clusters = [c for c in spec.clusters if not c.parent_path]

        def render_cluster(cluster: DiagramCluster, indent_level: int) -> None:
            indent = "    " * indent_level
            lines.append(f'{indent}with Cluster("{cluster.name}", direction="{cluster.direction}"):')
            
            # Nodes directly in this cluster
            # full cluster path is cluster.parent_path + (cluster.name,)
            current_path = cluster.parent_path + (cluster.name,)
            cluster_nodes = [n for n in spec.nodes if n.cluster_path == current_path]
            for n in cluster_nodes:
                lines.append(f'{indent}    {n.var_name} = {n.class_name}("{n.label}")')

            # Child clusters
            child_clusters = [
                c for c in spec.clusters if c.parent_path == current_path
            ]
            for child in child_clusters:
                render_cluster(child, indent_level + 1)

        # Render top clusters
        for tc in top_clusters:
            render_cluster(tc, 1)

        # Render root nodes
        for rn in root_nodes:
            lines.append(f'    {rn.var_name} = {rn.class_name}("{rn.label}")')

        if spec.edges:
            lines.append("")
            lines.append("    # Data Flow & Inter-Tier Pipes")
            for edge in spec.edges:
                edge_repr = cls._format_edge(edge)
                lines.append(f"    {edge_repr}")

        lines.append("")
        return "\n".join(lines)

    @classmethod
    def _format_edge(cls, edge: DiagramEdge) -> str:
        """Format a single DiagramEdge connection string."""
        if not edge.label and not edge.color and not edge.style:
            # Plain operator connection
            return f"{edge.source} {edge.direction} {edge.target}"

        params: list[str] = []
        if edge.label:
            params.append(f'label="{edge.label}"')
        if edge.color:
            params.append(f'color="{edge.color}"')
        if edge.style:
            params.append(f'style="{edge.style}"')

        edge_call = f"Edge({', '.join(params)})"
        return f"{edge.source} {edge.direction} {edge_call} {edge.direction} {edge.target}"

    @classmethod
    def lint_spec(cls, spec: DiagramSpec) -> DiagramValidationReport:
        """Statically lint an in-memory DiagramSpec against architecture best practices."""
        errors: list[str] = []
        warnings: list[str] = []

        providers_used = set()
        node_var_names = {n.var_name for n in spec.nodes}

        # 1. Check providers
        for node in spec.nodes:
            prov = node.provider.lower()
            providers_used.add(prov)
            if prov not in VALID_PROVIDERS:
                warnings.append(
                    f"Node '{node.var_name}' uses uncommon or custom provider '{node.provider}'."
                )

        # 2. Check for duplicate variable names
        var_counts: dict[str, int] = {}
        for node in spec.nodes:
            var_counts[node.var_name] = var_counts.get(node.var_name, 0) + 1
        for var_name, count in var_counts.items():
            if count > 1:
                errors.append(f"Duplicate node variable name '{var_name}' declared {count} times.")

        # 3. Check for orphan nodes (not present in any edge source or target)
        if spec.edges:
            connected_vars: set[str] = set()
            for edge in spec.edges:
                # Source/target might be list string or comma separated
                srcs = [s.strip() for s in edge.source.replace("[", "").replace("]", "").split(",")]
                tgts = [t.strip() for t in edge.target.replace("[", "").replace("]", "").split(",")]
                connected_vars.update(srcs)
                connected_vars.update(tgts)

            for node in spec.nodes:
                if node.var_name not in connected_vars:
                    warnings.append(f"Orphan node '{node.var_name}' ({node.label}) has no incoming or outgoing edges.")
        elif len(spec.nodes) > 1:
            warnings.append("Diagram specifies multiple nodes but defines zero connecting edges.")

        # 4. Check cluster depth
        max_depth = 0
        for cluster in spec.clusters:
            depth = len(cluster.parent_path) + 1
            if depth > max_depth:
                max_depth = depth
            if depth > 3:
                warnings.append(
                    f"Cluster '{cluster.name}' exceeds recommended nesting depth ({depth} > 3)."
                )

        # 5. Check headless show invariant
        if spec.show:
            warnings.append(
                "DiagramSpec has show=True. This causes blocking GUI popups in headless CI environments."
            )

        # 6. Check for multi-tier without clusters
        if len(spec.nodes) >= 6 and len(spec.clusters) == 0:
            warnings.append(
                "Complex diagram with >= 6 nodes lacks Cluster grouping (Monolithic Flat Canvas anti-pattern)."
            )

        is_valid = len(errors) == 0
        return DiagramValidationReport(
            valid=is_valid,
            errors=tuple(errors),
            warnings=tuple(warnings),
            node_count=len(spec.nodes),
            edge_count=len(spec.edges),
            cluster_count=len(spec.clusters),
            providers_used=tuple(sorted(providers_used)),
        )

    @classmethod
    def lint_script_code(cls, code_str: str) -> DiagramValidationReport:
        """Parse diagram Python script AST and check for syntax and anti-patterns."""
        errors: list[str] = []
        warnings: list[str] = []
        providers_used: set[str] = set()

        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            return DiagramValidationReport(
                valid=False,
                errors=(f"Python Syntax Error: {e}",),
                warnings=(),
                node_count=0,
                edge_count=0,
                cluster_count=0,
                providers_used=(),
            )

        # Inspect AST for show=True and providers
        has_diagram_call = False
        cluster_count = 0
        node_count = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("diagrams."):
                    parts = node.module.split(".")
                    if len(parts) >= 2:
                        providers_used.add(parts[1])

            elif isinstance(node, ast.With):
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        func = item.context_expr.func
                        func_name = getattr(func, "id", getattr(func, "attr", None))
                        if func_name == "Diagram":
                            has_diagram_call = True
                            # Check show keyword argument
                            for kw in item.context_expr.keywords:
                                if kw.arg == "show":
                                    if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                        warnings.append(
                                            "Diagram instantiated with show=True. Will block headless runners."
                                        )
                        elif func_name == "Cluster":
                            cluster_count += 1

            elif isinstance(node, ast.Call):
                func = node.func
                func_name = getattr(func, "id", getattr(func, "attr", None))
                if func_name not in ("Diagram", "Cluster", "Edge") and func_name is not None:
                    # Likely a node instantiation
                    node_count += 1

        if not has_diagram_call:
            errors.append("Script does not declare a 'with Diagram(...):' context.")

        is_valid = len(errors) == 0
        return DiagramValidationReport(
            valid=is_valid,
            errors=tuple(errors),
            warnings=tuple(warnings),
            node_count=node_count,
            edge_count=0,
            cluster_count=cluster_count,
            providers_used=tuple(sorted(providers_used)),
        )

    @classmethod
    def get_canonical_preset(cls, preset_name: str) -> DiagramSpec:
        """Retrieve pre-configured canonical system design diagram specifications."""
        clean_name = preset_name.strip().lower().replace("-", "_")

        if clean_name in ("three_tier_web_app", "three_tier", "web_app"):
            return DiagramSpec(
                title="Three-Tier Scaled Web Platform",
                filename="three_tier_web_app",
                direction="LR",
                outformat="png",
                show=False,
                clusters=(
                    DiagramCluster("Presentation Tier", parent_path=()),
                    DiagramCluster("Application Tier", parent_path=()),
                    DiagramCluster("Database Tier", parent_path=()),
                ),
                nodes=(
                    DiagramNode("aws", "network", "ELB", "ingress-lb", "lb", cluster_path=("Presentation Tier",)),
                    DiagramNode("aws", "compute", "EC2", "api-server-01", "api1", cluster_path=("Application Tier",)),
                    DiagramNode("aws", "compute", "EC2", "api-server-02", "api2", cluster_path=("Application Tier",)),
                    DiagramNode("aws", "database", "RDS", "primary-db", "db_primary", cluster_path=("Database Tier",)),
                    DiagramNode("aws", "database", "RDS", "read-replica", "db_replica", cluster_path=("Database Tier",)),
                ),
                edges=(
                    DiagramEdge("lb", "api1", direction=">>", label="HTTPS"),
                    DiagramEdge("lb", "api2", direction=">>", label="HTTPS"),
                    DiagramEdge("api1", "db_primary", direction=">>", label="SQL Write", color="darkgreen"),
                    DiagramEdge("api2", "db_replica", direction=">>", label="SQL Read", color="blue", style="dashed"),
                    DiagramEdge("db_primary", "db_replica", direction="-", label="Replication", style="dotted"),
                ),
            )

        if clean_name in ("event_driven_microservices", "event_driven", "microservices"):
            return DiagramSpec(
                title="Event-Driven Microservices Architecture",
                filename="event_driven_architecture",
                direction="LR",
                outformat="png",
                show=False,
                clusters=(
                    DiagramCluster("API Gateway Tier", parent_path=()),
                    DiagramCluster("Streaming & Queue Tier", parent_path=()),
                    DiagramCluster("Worker Services", parent_path=()),
                    DiagramCluster("Persistence Tier", parent_path=()),
                ),
                nodes=(
                    DiagramNode("aws", "network", "APIGateway", "api-gateway", "gateway", cluster_path=("API Gateway Tier",)),
                    DiagramNode("aws", "integration", "SQS", "events-queue", "queue", cluster_path=("Streaming & Queue Tier",)),
                    DiagramNode("aws", "compute", "Lambda", "order-processor", "processor", cluster_path=("Worker Services",)),
                    DiagramNode("aws", "database", "Dynamodb", "orders-table", "dynamo", cluster_path=("Persistence Tier",)),
                    DiagramNode("aws", "storage", "S3", "event-archive", "s3_archive", cluster_path=("Persistence Tier",)),
                ),
                edges=(
                    DiagramEdge("gateway", "queue", direction=">>", label="Push Event", color="firebrick"),
                    DiagramEdge("queue", "processor", direction=">>", label="Poll Batch", style="dashed"),
                    DiagramEdge("processor", "dynamo", direction=">>", label="Store State", color="darkgreen"),
                    DiagramEdge("processor", "s3_archive", direction=">>", label="Raw Backup", style="dotted"),
                ),
            )

        if clean_name in ("kubernetes_cluster", "k8s_cluster", "k8s"):
            return DiagramSpec(
                title="Kubernetes Ingress and Pod Architecture",
                filename="k8s_microservices",
                direction="TB",
                outformat="png",
                show=False,
                clusters=(
                    DiagramCluster("Cluster Boundary", parent_path=()),
                    DiagramCluster("Default Namespace", parent_path=("Cluster Boundary",)),
                ),
                nodes=(
                    DiagramNode("k8s", "network", "Ing", "cluster-ingress", "ingress", cluster_path=("Cluster Boundary",)),
                    DiagramNode("k8s", "network", "Svc", "api-service", "svc", cluster_path=("Cluster Boundary", "Default Namespace")),
                    DiagramNode("k8s", "compute", "Pod", "api-pod-1", "pod1", cluster_path=("Cluster Boundary", "Default Namespace")),
                    DiagramNode("k8s", "compute", "Pod", "api-pod-2", "pod2", cluster_path=("Cluster Boundary", "Default Namespace")),
                ),
                edges=(
                    DiagramEdge("ingress", "svc", direction=">>", label="Route /api", color="purple"),
                    DiagramEdge("svc", "pod1", direction=">>", label="Round Robin"),
                    DiagramEdge("svc", "pod2", direction=">>", label="Round Robin"),
                ),
            )

        raise KeyError(
            f"Unknown preset '{preset_name}'. Available presets: 'three_tier_web_app', 'event_driven_microservices', 'kubernetes_cluster'."
        )
