"""Run namespaces and supervised agent worker dispatching."""

from __future__ import annotations

import time
import uuid

import structlog

from harness.services.orca_bridge import (
    OrcaRunConfig,
    OrcaRunInfo,
    OrcaWorkerConfig,
    OrcaWorkerDispatchReceipt,
)

logger = structlog.get_logger(__name__)


class OrcaWorkerMixin:
    """Provides Run namespace binding and supervised agent worker dispatching."""

    def create_run(self, config: OrcaRunConfig) -> OrcaRunInfo:
        """Create and bind an orchestration coordinator Run namespace."""
        if self.is_cli_available:
            args = [
                "orchestration",
                "run-create",
                "--objective",
                config.objective,
                "--from",
                config.from_handle,
            ]
            data = self._run_cli(args)
            run_data = data.get("run") or data
            return OrcaRunInfo(
                run_id=run_data.get("id", f"run-{uuid.uuid4().hex[:8]}"),
                objective=config.objective,
                coordinator_terminal=config.from_handle,
                status=run_data.get("status", "active"),
                created_at=time.time(),
            )

        # In-memory fallback
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        info = OrcaRunInfo(
            run_id=run_id,
            objective=config.objective,
            coordinator_terminal=config.from_handle,
            status="active",
            created_at=time.time(),
        )
        self._mock_runs[run_id] = info
        logger.info("Created mock orchestration run", run_id=run_id)
        return info

    def start_worker(self, config: OrcaWorkerConfig) -> OrcaWorkerDispatchReceipt:
        """Start a supervised agent worker in a dedicated worktree with injected authority."""
        if self.is_cli_available:
            args = ["orchestration", "worker-start"]
            if config.task_id:
                args.extend(["--task", config.task_id])
            elif config.spec:
                args.extend(["--spec", config.spec])
            args.extend(["--agent", config.agent, "--worktree", config.worktree])
            if config.model:
                args.extend(["--model", config.model])
            if config.effort:
                args.extend(["--effort", config.effort])
            args.extend(["--timeout-ms", str(config.timeout_ms)])

            data = self._run_cli(args)
            return OrcaWorkerDispatchReceipt(
                dispatch_id=data.get("dispatchId", f"dispatch-{uuid.uuid4().hex[:8]}"),
                task_id=data.get(
                    "taskId", config.task_id or f"task-{uuid.uuid4().hex[:8]}"
                ),
                terminal_handle=data.get("terminalHandle", f"term-{config.agent}"),
                worktree_id=data.get("worktreeId", "repo-default::/worktree"),
                status=data.get("status", "ready"),
                preamble=data.get("preamble"),
            )

        # In-memory fallback
        dispatch_id = f"dispatch-{uuid.uuid4().hex[:8]}"
        task_id = config.task_id or f"task-{uuid.uuid4().hex[:8]}"
        terminal_handle = f"term-{config.agent}-{uuid.uuid4().hex[:4]}"
        worktree_id = f"repo-mock::/mock/{terminal_handle}"

        preamble = (
            f"ORCA SUPERVISED WORKER PREAMBLE\n"
            f"TASK_ID={task_id}\n"
            f"DISPATCH_ID={dispatch_id}\n"
            f"AGENT={config.agent}\n"
            f"Send 'worker_done --outcome succeeded' upon completion."
        )

        receipt = OrcaWorkerDispatchReceipt(
            dispatch_id=dispatch_id,
            task_id=task_id,
            terminal_handle=terminal_handle,
            worktree_id=worktree_id,
            status="ready",
            preamble=preamble,
        )
        self._mock_dispatches[dispatch_id] = receipt
        logger.info(
            "Started mock supervised worker", dispatch_id=dispatch_id, task_id=task_id
        )
        return receipt
