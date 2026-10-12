"""Session hierarchy, tree aggregation, and immutable snapshot mixin."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from harness.agent.session.models import SessionTreeNode, SessionTreeSnapshot

if TYPE_CHECKING:
    from harness.agent.session.models import AgentSession
    from harness.agent.session.store import AgentSessionStore


class SessionHierarchyMixin:
    """Provides recursive subtree aggregation and immutable tree snapshots."""

    store: AgentSessionStore

    async def get_subtree_metrics(self, session_id: str) -> dict[str, Any]:
        """Compute recursive aggregations (tokens, steps, duration, statuses) across a session subtree."""
        tree = await self.get_session_tree(session_id)
        if not tree:
            return {
                "total_sessions": 0,
                "total_tokens": 0,
                "total_steps": 0,
                "total_duration": 0.0,
                "completed_count": 0,
                "failed_count": 0,
            }

        total_tokens = 0
        total_steps = 0
        completed_count = 0
        failed_count = 0
        total_sessions = 0
        min_created = float("inf")
        max_completed = 0.0

        def _collect(node: dict[str, Any]) -> None:
            nonlocal total_tokens, total_steps, completed_count, failed_count, total_sessions, min_created, max_completed
            total_sessions += 1
            total_tokens += int(node.get("total_tokens", 0) or 0)
            total_steps += len(node.get("steps", []) or [])
            st = node.get("status", "")
            if st == "completed":
                completed_count += 1
            elif st in ("error", "failed", "max_steps_reached"):
                failed_count += 1

            cr = float(node.get("created_at", 0) or 0)
            if cr > 0 and cr < min_created:
                min_created = cr
            cm = float(node.get("completed_at", 0) or node.get("updated_at", 0) or 0)
            if cm > max_completed:
                max_completed = cm

            for child in (node.get("children") or []):
                _collect(child)

        _collect(tree)
        duration = max(0.0, round(max_completed - min_created, 3)) if min_created < float("inf") else 0.0

        return {
            "total_sessions": total_sessions,
            "total_tokens": total_tokens,
            "total_steps": total_steps,
            "total_duration": duration,
            "completed_count": completed_count,
            "failed_count": failed_count,
        }

    async def get_session_tree(self, session_id: str) -> dict[str, Any] | None:
        """Recursively build hierarchical session execution tree with all child sessions and metrics."""
        session = await self.store.get(session_id)
        if not session:
            return None

        tree = session.to_dict()
        children: list[dict[str, Any]] = []
        for child_id in session.children_session_ids:
            child_tree = await self.get_session_tree(child_id)
            if child_tree:
                children.append(child_tree)

        tree["children"] = children

        # Compute rollups
        total_subtree_tokens = tree.get("total_tokens", 0)
        total_subtree_steps = len(tree.get("steps", []))
        for c in children:
            sub = c.get("subtree_metrics", {})
            total_subtree_tokens += sub.get("total_tokens", c.get("total_tokens", 0))
            total_subtree_steps += sub.get("total_steps", len(c.get("steps", [])))

        tree["subtree_metrics"] = {
            "total_tokens": total_subtree_tokens,
            "total_steps": total_subtree_steps,
            "child_count": len(children),
        }
        return tree

    async def get_tree_snapshot(self, session_id: str) -> SessionTreeSnapshot | None:
        """Construct an immutable, slotted SessionTreeSnapshot for a session hierarchy."""
        session = await self.store.get(session_id)
        if not session:
            return None

        total_sessions = 0
        total_tokens = 0
        total_steps = 0
        completed_count = 0
        failed_count = 0
        min_created = float("inf")
        max_completed = 0.0
        max_depth = 0

        async def _build_node(sess: AgentSession, current_depth: int) -> SessionTreeNode:
            nonlocal total_sessions, total_tokens, total_steps, completed_count, failed_count, min_created, max_completed, max_depth
            total_sessions += 1
            if current_depth > max_depth:
                max_depth = current_depth

            sess_tokens = int(sess.total_tokens or 0)
            sess_steps = len(sess.steps or [])
            total_tokens += sess_tokens
            total_steps += sess_steps

            if sess.status == "completed":
                completed_count += 1
            elif sess.status in ("error", "failed", "max_steps_reached"):
                failed_count += 1

            if sess.created_at and sess.created_at < min_created:
                min_created = sess.created_at
            end_t = sess.completed_at or sess.updated_at or sess.created_at
            if end_t and end_t > max_completed:
                max_completed = end_t

            children_nodes: list[SessionTreeNode] = []
            sub_tokens = sess_tokens
            sub_steps = sess_steps

            for child_id in sess.children_session_ids:
                child_sess = await self.store.get(child_id)
                if child_sess:
                    child_node = await _build_node(child_sess, current_depth + 1)
                    children_nodes.append(child_node)
                    sub_tokens += child_node.subtree_tokens
                    sub_steps += child_node.subtree_steps

            return SessionTreeNode(
                session_id=sess.session_id,
                task=sess.task,
                status=sess.status,
                created_at=sess.created_at,
                updated_at=sess.updated_at,
                completed_at=sess.completed_at,
                final_answer=sess.final_answer,
                total_tokens=sess_tokens,
                steps_count=sess_steps,
                role=sess.role,
                node_id=sess.node_id,
                parent_session_id=sess.parent_session_id,
                children=tuple(children_nodes),
                depth=current_depth,
                subtree_tokens=sub_tokens,
                subtree_steps=sub_steps,
            )

        root_node = await _build_node(session, 0)
        duration = max(0.0, round(max_completed - min_created, 3)) if min_created < float("inf") else 0.0

        metrics = {
            "total_sessions": total_sessions,
            "total_tokens": total_tokens,
            "total_steps": total_steps,
            "total_duration": duration,
            "max_depth": max_depth,
            "completed_count": completed_count,
            "failed_count": failed_count,
        }

        return SessionTreeSnapshot(
            root=root_node,
            total_sessions=total_sessions,
            total_tokens=total_tokens,
            total_steps=total_steps,
            total_duration=duration,
            max_depth=max_depth,
            completed_count=completed_count,
            failed_count=failed_count,
            metrics=metrics,
        )
