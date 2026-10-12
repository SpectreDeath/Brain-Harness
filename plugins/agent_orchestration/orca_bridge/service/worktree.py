"""Worktree operations for Orca Git sandbox management."""

from __future__ import annotations

import structlog

from harness.services.orca_bridge import OrcaWorktreeConfig, OrcaWorktreeInfo

logger = structlog.get_logger(__name__)


class OrcaWorktreeMixin:
    """Provides Git worktree creation and listing operations."""

    def create_worktree(self, config: OrcaWorktreeConfig) -> OrcaWorktreeInfo:
        """Create or provision an isolated Git worktree."""
        if self.is_cli_available:
            args = ["worktree", "create", "--name", config.name]
            if config.repo_id:
                args.extend(["--repo", f"id:{config.repo_id}"])
            if config.agent:
                args.extend(["--agent", config.agent])
            if config.prompt:
                args.extend(["--prompt", config.prompt])
            if config.no_parent:
                args.append("--no-parent")
            elif config.parent_worktree:
                args.extend(["--parent-worktree", config.parent_worktree])
            if config.base_branch:
                args.extend(["--base-branch", config.base_branch])

            data = self._run_cli(args)
            wt = data.get("worktree") or data
            return OrcaWorktreeInfo(
                worktree_id=wt.get("id", f"repo-default::{config.name}"),
                repo_id=wt.get("repoId", config.repo_id or "repo-default"),
                path=wt.get("path", f"/worktrees/{config.name}"),
                branch=wt.get("branch", config.name),
                display_name=wt.get("displayName", config.name),
                status=wt.get("status", "active"),
                agent_handle=wt.get("agentHandle"),
            )

        # In-memory fallback
        repo_id = config.repo_id or "repo-local"
        path = f"/mock/worktrees/{config.name}"
        wt_id = f"{repo_id}::{path}"
        info = OrcaWorktreeInfo(
            worktree_id=wt_id,
            repo_id=repo_id,
            path=path,
            branch=config.name,
            display_name=config.name,
            status="active",
            agent_handle=f"agent-{config.name}",
        )
        self._mock_worktrees[wt_id] = info
        logger.info("Created mock worktree", worktree_id=wt_id)
        return info

    def list_worktrees(self, repo_id: str | None = None) -> list[OrcaWorktreeInfo]:
        """List active and detected Git worktrees."""
        if self.is_cli_available:
            args = ["worktree", "list"]
            if repo_id:
                args.extend(["--repo", f"id:{repo_id}"])
            data = self._run_cli(args)
            items = data.get("worktrees") or (data if isinstance(data, list) else [])
            results: list[OrcaWorktreeInfo] = []
            for item in items:
                wt_id = item.get("id", "unknown::/unknown")
                results.append(
                    OrcaWorktreeInfo(
                        worktree_id=wt_id,
                        repo_id=item.get("repoId", "unknown"),
                        path=item.get("path", ""),
                        branch=item.get("branch", ""),
                        display_name=item.get("displayName", ""),
                        status=item.get("status", "active"),
                        agent_handle=item.get("agentHandle"),
                    )
                )
            return results

        # In-memory fallback
        if repo_id:
            return [wt for wt in self._mock_worktrees.values() if wt.repo_id == repo_id]
        return list(self._mock_worktrees.values())
