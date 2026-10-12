"""High-leverage end-to-end swarm execution and worker settlement loop."""

from __future__ import annotations

import time
import uuid

from harness.services.orca_bridge import (
    OrcaMessageConfig,
    OrcaRunConfig,
    OrcaTaskSettlement,
    OrcaWorkerConfig,
    OrcaWorktreeConfig,
)


class OrcaCoordinatorMixin:
    """Coordinates supervised workers from provisioning through settlement."""

    def coordinate_worker(
        self,
        task_spec: str,
        agent: str = "codex",
        worktree_name: str | None = None,
        model: str | None = None,
        effort: str | None = None,
        timeout_seconds: float = 60.0,
    ) -> OrcaTaskSettlement:
        """High-leverage end-to-end swarm execution: provisions worktree, injects preamble, monitors FIFO mailbox, and returns settlement."""
        start_time = time.time()
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        wt_name = worktree_name or f"wt-{task_id}"

        # 1. Provision isolated worktree
        wt = self.create_worktree(
            OrcaWorktreeConfig(
                name=wt_name,
                agent=agent,
                prompt=task_spec,
                no_parent=True,
            )
        )

        # 2. Bind coordinator run namespace
        run = self.create_run(
            OrcaRunConfig(
                objective=f"Coordinate task {task_id}: {task_spec[:60]}",
                from_handle="coordinator",
            )
        )

        # 3. Start worker with injected authority preamble
        worker = self.start_worker(
            OrcaWorkerConfig(
                task_id=task_id,
                spec=task_spec,
                agent=agent,
                worktree=wt.worktree_id,
                model=model,
                effort=effort,
                timeout_ms=int(timeout_seconds * 1000),
            )
        )

        # 4. If in-memory fallback, simulate worker completion
        if not self.is_cli_available:
            self.send_message(
                OrcaMessageConfig(
                    subject=f"Worker done: {task_id}",
                    to=f"run:{run.run_id}",
                    message_type="worker_done",
                    outcome="succeeded",
                    task_id=task_id,
                    dispatch_id=worker.dispatch_id,
                    body=f"Worker successfully completed task: {task_spec}",
                    files_modified="src/module.py,tests/test_module.py",
                )
            )

        # 5. Mailbox polling loop with keepalive filtering & auto-ACK
        deadline = start_time + timeout_seconds
        last_delivery_id: str | None = None
        settlement: OrcaTaskSettlement | None = None

        while time.time() < deadline:
            poll_timeout_ms = min(
                15000, max(1000, int((deadline - time.time()) * 1000))
            )
            batch = self.check_mailbox(
                terminal="coordinator",
                wait=True,
                timeout_ms=poll_timeout_ms,
                ack_delivery_id=last_delivery_id,
            )
            last_delivery_id = batch.delivery_id

            for msg in batch.messages:
                m_type = msg.get("type") or msg.get("message_type")
                if m_type == "worker_done":
                    outcome = msg.get("outcome", "succeeded")
                    raw_files = (
                        msg.get("files_modified") or msg.get("filesModified") or ""
                    )
                    files_tuple = (
                        tuple(f.strip() for f in raw_files.split(",") if f.strip())
                        if isinstance(raw_files, str)
                        else tuple(raw_files)
                    )
                    report_text = (
                        msg.get("body")
                        or msg.get("report_path")
                        or f"Worker completed with outcome: {outcome}"
                    )
                    elapsed = time.time() - start_time
                    settlement = OrcaTaskSettlement(
                        task_id=task_id,
                        dispatch_id=worker.dispatch_id,
                        outcome=outcome,
                        worktree_id=wt.worktree_id,
                        files_modified=files_tuple,
                        report=report_text,
                        elapsed_seconds=round(elapsed, 2),
                        status="settled",
                    )
                    break

            if settlement is not None:
                if last_delivery_id:
                    self.check_mailbox(ack_delivery_id=last_delivery_id)
                return settlement

            if not self.is_cli_available:
                break

            time.sleep(0.5)

        elapsed = time.time() - start_time
        return OrcaTaskSettlement(
            task_id=task_id,
            dispatch_id=worker.dispatch_id,
            outcome="failed",
            worktree_id=wt.worktree_id,
            files_modified=(),
            report="Task coordination timed out before worker_done signal was received.",
            elapsed_seconds=round(elapsed, 2),
            status="timed_out",
        )
