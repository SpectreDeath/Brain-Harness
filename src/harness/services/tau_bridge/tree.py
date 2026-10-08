"""Session tree DAG resolver, ancestry traversal, fork point discovery, and ASCII visualization."""

from __future__ import annotations

from typing import Any

from harness.services.tau_bridge.models import BranchPath, SessionNode


class SessionTreeResolver:
    """Traverses, analyzes, and visualizes branchable Pi-style session tree DAGs."""

    @staticmethod
    def parse_entry(entry: dict[str, Any] | SessionNode) -> SessionNode:
        """Parse raw dictionary or node into verified SessionNode."""
        if isinstance(entry, SessionNode):
            return entry
        tool_calls = tuple(entry.get("tool_calls") or ())
        return SessionNode(
            id=str(entry.get("id", "")),
            parent_id=entry.get("parent_id"),
            type=str(entry.get("type", "message")),
            role=str(entry.get("role", "user")),
            content=str(entry.get("content", "")),
            tool_calls=tool_calls,
            tool_call_id=entry.get("tool_call_id"),
            timestamp=str(entry.get("timestamp", "")),
        )

    @classmethod
    def resolve_path(
        cls, entries: list[dict[str, Any] | SessionNode], target_id: str
    ) -> BranchPath:
        """Resolve linear path from root to target_id via hash indexing with cycle detection."""
        nodes: dict[str, SessionNode] = {}
        children_count: dict[str, int] = {}

        for raw in entries:
            node = cls.parse_entry(raw)
            nodes[node.id] = node
            if node.parent_id:
                children_count[node.parent_id] = (
                    children_count.get(node.parent_id, 0) + 1
                )

        if target_id not in nodes:
            raise KeyError(f"Target entry id '{target_id}' not found in session tree.")

        # Reconstruct path by walking up parents
        path: list[SessionNode] = []
        curr_id: str | None = target_id
        visited: set[str] = set()

        while curr_id is not None:
            if curr_id in visited:
                raise ValueError(f"Cycle detected in session tree at id '{curr_id}'.")
            visited.add(curr_id)

            node = nodes.get(curr_id)
            if node is None:
                # Parent referenced does not exist in graph; stop at root
                break
            path.append(node)
            curr_id = node.parent_id

        path.reverse()

        branch_points = sum(1 for count in children_count.values() if count > 1)

        return BranchPath(
            target_id=target_id,
            path_entries=tuple(path),
            depth=len(path),
            total_entries=len(nodes),
            branch_count=branch_points,
        )

    @classmethod
    def find_leaves(
        cls, entries: list[dict[str, Any] | SessionNode]
    ) -> list[SessionNode]:
        """Discover active conversation branch tips / leaf nodes."""
        nodes: dict[str, SessionNode] = {}
        parents: set[str] = set()

        for raw in entries:
            node = cls.parse_entry(raw)
            nodes[node.id] = node
            if node.parent_id:
                parents.add(node.parent_id)

        # Leaves are nodes whose IDs are never a parent of another node
        return [node for node_id, node in nodes.items() if node_id not in parents]

    @classmethod
    def find_fork_points(
        cls, entries: list[dict[str, Any] | SessionNode]
    ) -> dict[str, list[str]]:
        """Identify branch points where a parent has two or more direct children."""
        children_map: dict[str, list[str]] = {}

        for raw in entries:
            node = cls.parse_entry(raw)
            if node.parent_id:
                children_map.setdefault(node.parent_id, []).append(node.id)

        return {
            parent_id: kids
            for parent_id, kids in children_map.items()
            if len(kids) > 1
        }

    @classmethod
    def render_ascii_tree(
        cls,
        entries: list[dict[str, Any] | SessionNode],
        root_id: str | None = None,
    ) -> str:
        """Render deterministic ASCII DAG tree representation for terminal inspection."""
        if not entries:
            return "(Empty session tree)\n"

        nodes: dict[str, SessionNode] = {}
        children: dict[str | None, list[str]] = {}

        for raw in entries:
            node = cls.parse_entry(raw)
            nodes[node.id] = node
            children.setdefault(node.parent_id, []).append(node.id)

        roots = [root_id] if root_id and root_id in nodes else children.get(None, [])
        if not roots:
            # Fall back to any node with missing parent
            all_ids = set(nodes.keys())
            roots = [
                n.id for n in nodes.values() if n.parent_id not in all_ids
            ]

        lines: list[str] = []

        def _walk(node_id: str, prefix: str = "", is_last: bool = True) -> None:
            node = nodes[node_id]
            connector = "└── " if is_last else "├── "
            snippet = node.content.replace("\n", " ").strip()
            if len(snippet) > 40:
                snippet = snippet[:37] + "..."
            calls_tag = f" [calls:{len(node.tool_calls)}]" if node.tool_calls else ""
            lines.append(
                f"{prefix}{connector}[{node.id}] {node.role}: {snippet}{calls_tag}"
            )

            child_ids = children.get(node_id, [])
            new_prefix = prefix + ("    " if is_last else "│   ")
            for idx, c_id in enumerate(child_ids):
                _walk(c_id, new_prefix, idx == len(child_ids) - 1)

        for r_idx, r_id in enumerate(roots):
            _walk(r_id, "", r_idx == len(roots) - 1)

        return "\n".join(lines) + "\n"


__all__ = [
    "SessionTreeResolver",
]
