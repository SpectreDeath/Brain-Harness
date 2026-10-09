"""Transactional tool execution boundaries and workspace checkpointing for ReAct agents."""

from __future__ import annotations

from typing import Any

from harness.kernel.context import ServiceContext
from harness.services.arch_linter import (
    ArchLinterService,
    resolve_arch_linter,
)
from harness.services.filesystem_git import (
    FILESYSTEM_GIT_KEY,
    FilesystemGitService,
)
from harness.services.tools import ToolRegistry


async def invoke_tool_transactional(
    context: ServiceContext,
    tools: ToolRegistry,
    action_name: str,
    action_input: dict[str, Any],
    active_skills: list[str] | None = None,
    state_holder: Any = None,
) -> Any:
    """Invoke tool inside a transactional boundary with git checkpointing and lint verification.

    Conforms to Rule 8 (workspace checkpointing), Rule 16 (in-flight lint self-repair),
    and Rule 21 (anti-pattern action gating).
    """
    git_svc: FilesystemGitService | None = context.optional(FILESYSTEM_GIT_KEY)
    linter_svc: ArchLinterService = resolve_arch_linter(context)

    target_file_path = (
        action_input.get("path")
        or action_input.get("file_path")
        or action_input.get("target_file")
    )

    # Rule 16 & Rule 21: Active Anti-Pattern & Invariant Interception before tool execution
    try:
        from harness.services.skill_graph import resolve_skill_intelligence

        intel = resolve_skill_intelligence(context)
        gate = intel.evaluate_action_gate(
            action_name, action_input, active_skills=active_skills or []
        )
        if gate.is_blocked:
            return gate.to_observation()
    except Exception:
        pass

    async with context.transaction() as tx:
        prev_ctx = getattr(state_holder, "context", context) if state_holder else context
        if state_holder is not None:
            state_holder.context = tx
        try:
            obs = await tools.invoke(action_name, action_input)
            if isinstance(obs, dict):
                is_error = obs.get("status") == "error" or "error" in obs
                res_val = obs.get("result")
                if isinstance(res_val, dict) and (
                    res_val.get("status") == "error" or "error" in res_val
                ):
                    is_error = True

                # Lint validation on edited file (Rule 16)
                if not is_error and target_file_path and linter_svc:
                    lint_res = linter_svc.lint_file(str(target_file_path))
                    if not lint_res.is_clean:
                        obs["lint_diagnostics"] = lint_res.formatted_summary

                if is_error:
                    await tx.dispose()
                    if git_svc:
                        git_svc.rollback_transaction()
                else:
                    if git_svc:
                        git_svc.commit_transaction(
                            f"chore(agent): tool {action_name}"
                        )
            return obs
        except Exception as err:
            await tx.dispose()
            if git_svc:
                git_svc.rollback_transaction()
            return {"status": "error", "error": f"Tool execution failed: {err}"}
        finally:
            if state_holder is not None:
                state_holder.context = prev_ctx
