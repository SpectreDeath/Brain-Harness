"""Implementation of OrcaBridgeService providing CLI execution and state tracking."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import uuid
from typing import Any

import structlog

from harness.services.orca_bridge import (
    OrcaBridgeService,
    OrcaDeliveryBatch,
    OrcaMessageConfig,
    OrcaRunConfig,
    OrcaRunInfo,
    OrcaTaskSettlement,
    OrcaWorkerConfig,
    OrcaWorkerDispatchReceipt,
    OrcaWorktreeConfig,
    OrcaWorktreeInfo,
)

logger = structlog.get_logger(__name__)


class DefaultOrcaBridgeService(OrcaBridgeService):
    """Core implementation of OrcaBridgeService wrapping the orca CLI with in-memory fallback."""

    def __init__(self, orca_bin: str | None = None) -> None:
        self._orca_bin = (
            orca_bin
            or os.environ.get("ORCA_BIN")
            or shutil.which("orca")
            or shutil.which("orca.cmd")
        )
        self._mock_worktrees: dict[str, OrcaWorktreeInfo] = {}
        self._mock_runs: dict[str, OrcaRunInfo] = {}
        self._mock_dispatches: dict[str, OrcaWorkerDispatchReceipt] = {}
        self._mock_inbox: list[dict[str, Any]] = []

    @property
    def is_cli_available(self) -> bool:
        """Return True if the orca CLI binary is found on PATH or configured."""
        return self._orca_bin is not None

    def _run_cli(self, args: list[str]) -> dict[str, Any]:
        """Execute orca CLI command with JSON formatting and UTF-8 encoding (Rule 23, Rule 14)."""
        if not self._orca_bin:
            raise FileNotFoundError("Orca CLI executable not found on PATH")

        cmd = [self._orca_bin, *args, "--json"]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        try:
            stdout, stderr = proc.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            raise TimeoutError(f"Orca command timed out after 60s: {' '.join(cmd)}")
        finally:
            if proc.stdin:
                proc.stdin.close()
            if proc.stdout:
                proc.stdout.close()
            if proc.stderr:
                proc.stderr.close()

        if proc.returncode != 0:
            logger.warning(
                "Orca CLI returned non-zero", code=proc.returncode, stderr=stderr
            )
            raise RuntimeError(
                f"Orca command failed ({proc.returncode}): {stderr.strip()}"
            )

        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Failed to parse Orca CLI output as JSON: {stdout}"
            ) from exc

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
            f"ORCA SUPERVISED WORKER PREAMBLE\\n"
            f"TASK_ID={task_id}\\n"
            f"DISPATCH_ID={dispatch_id}\\n"
            f"AGENT={config.agent}\\n"
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

    def check_mailbox(
        self,
        terminal: str | None = None,
        wait: bool = False,
        timeout_ms: int = 15000,
        types: str | None = None,
        ack_delivery_id: str | None = None,
    ) -> OrcaDeliveryBatch:
        """Query or await the FIFO coordinator mailbox for incoming agent reports."""
        if self.is_cli_available:
            args = ["orchestration", "check"]
            if terminal:
                args.extend(["--terminal", terminal])
            if wait:
                args.append("--wait")
            if timeout_ms:
                args.extend(["--timeout-ms", str(timeout_ms)])
            if types:
                args.extend(["--types", types])
            if ack_delivery_id:
                args.extend(["--ack", ack_delivery_id])

            data = self._run_cli(args)
            messages = tuple(data.get("messages", []))
            return OrcaDeliveryBatch(
                delivery_id=data.get("deliveryId", f"deliv-{uuid.uuid4().hex[:8]}"),
                messages=messages,
                satisfied=data.get("satisfied", True),
                has_keepalive=data.get("hasKeepalive", False),
            )

        # In-memory fallback
        delivery_id = f"deliv-{uuid.uuid4().hex[:8]}"
        batch = tuple(self._mock_inbox)
        if ack_delivery_id:
            self._mock_inbox.clear()
        return OrcaDeliveryBatch(
            delivery_id=delivery_id,
            messages=batch,
            satisfied=True,
            has_keepalive=False,
        )

    def send_message(self, config: OrcaMessageConfig) -> dict[str, Any]:
        """Send an inter-agent message or post a worker settlement signal."""
        if self.is_cli_available:
            args = ["orchestration", "send", "--subject", config.subject]
            if config.to:
                args.extend(["--to", config.to])
            if config.body:
                args.extend(["--body", config.body])
            if config.message_type:
                args.extend(["--type", config.message_type])
            if config.task_id:
                args.extend(["--task-id", config.task_id])
            if config.dispatch_id:
                args.extend(["--dispatch-id", config.dispatch_id])
            if config.outcome:
                args.extend(["--outcome", config.outcome])
            if config.files_modified:
                args.extend(["--files-modified", config.files_modified])
            if config.report_path:
                args.extend(["--report-path", config.report_path])

            return self._run_cli(args)

        # In-memory fallback
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        record = {
            "id": msg_id,
            "subject": config.subject,
            "to": config.to,
            "body": config.body,
            "type": config.message_type,
            "taskId": config.task_id,
            "dispatchId": config.dispatch_id,
            "outcome": config.outcome,
            "files_modified": config.files_modified,
            "report_path": config.report_path,
            "timestamp": time.time(),
        }
        self._mock_inbox.append(record)
        logger.info(
            "Delivered mock inter-agent message", msg_id=msg_id, subject=config.subject
        )
        return {"status": "ok", "messageId": msg_id, "accepted": True}

    def send_terminal_input(
        self, terminal: str, text: str, enter: bool = True
    ) -> dict[str, Any]:
        """Deliver input directly to an active agent terminal PTY."""
        if self.is_cli_available:
            args = ["terminal", "send", "--terminal", terminal, "--text", text]
            if enter:
                args.append("--enter")
            return self._run_cli(args)

        # In-memory fallback
        logger.info(
            "Sent mock terminal input", terminal=terminal, text=text, enter=enter
        )
        return {"status": "ok", "terminal": terminal, "delivered": True}

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
