"""Orca Bridge Service protocol, slotted/frozen domain models, and ServiceKey."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey


@dataclass(slots=True, frozen=True)
class OrcaWorktreeConfig:
    """Configuration for creating or targeting an Orca-managed Git worktree (Rule 12)."""

    name: str
    repo_id: str | None = None
    agent: str | None = None  # "codex", "claude", "opencode", "pi"
    prompt: str | None = None
    parent_worktree: str | None = None
    no_parent: bool = True
    base_branch: str | None = None

    def __post_init__(self) -> None:
        assert self.name and len(self.name.strip()) > 0, (
            "Worktree name must be non-empty"
        )


@dataclass(slots=True, frozen=True)
class OrcaWorktreeInfo:
    """Record describing an Orca-tracked Git worktree (Rule 12)."""

    worktree_id: str  # Format: "<repoId>::<worktreePath>"
    repo_id: str
    path: str
    branch: str
    display_name: str
    status: str = "active"
    agent_handle: str | None = None

    def __post_init__(self) -> None:
        assert "::" in self.worktree_id, (
            f"Orca worktree ID must follow '<repoId>::<path>' format: {self.worktree_id}"
        )


@dataclass(slots=True, frozen=True)
class OrcaRunConfig:
    """Configuration for binding an orchestration coordinator Run namespace (Rule 12)."""

    objective: str
    from_handle: str = "coordinator"

    def __post_init__(self) -> None:
        assert self.objective and len(self.objective.strip()) > 0, (
            "Run objective must be non-empty"
        )


@dataclass(slots=True, frozen=True)
class OrcaRunInfo:
    """Record describing an active orchestration Run (Rule 12)."""

    run_id: str
    objective: str
    coordinator_terminal: str
    status: str = "active"
    created_at: float = 0.0

    def __post_init__(self) -> None:
        assert self.run_id and len(self.run_id.strip()) > 0, "Run ID must be non-empty"


@dataclass(slots=True, frozen=True)
class OrcaWorkerConfig:
    """Configuration for starting a supervised agent worker in Orca (Rule 12)."""

    task_id: str | None = None
    spec: str | None = None
    agent: str = "codex"  # "codex", "claude", "opencode", "pi"
    worktree: str = (
        "new-top-level"  # "current", "new-child", "new-top-level", or exact selector
    )
    model: str | None = None
    effort: str | None = None  # "low", "medium", "high", "xhigh"
    timeout_ms: int = 60000

    def __post_init__(self) -> None:
        assert self.task_id or self.spec, "Worker requires either task_id or spec"
        assert self.agent in ("codex", "claude", "opencode", "pi", "copilot"), (
            f"Unsupported agent: {self.agent}"
        )


@dataclass(slots=True, frozen=True)
class OrcaWorkerDispatchReceipt:
    """Record returned when a supervised worker dispatch is registered (Rule 12)."""

    dispatch_id: str
    task_id: str
    terminal_handle: str
    worktree_id: str
    status: str = "ready"  # "ready", "failed", "outcome_unknown"
    preamble: str | None = None

    def __post_init__(self) -> None:
        assert self.dispatch_id and len(self.dispatch_id.strip()) > 0, (
            "Dispatch ID must be non-empty"
        )


@dataclass(slots=True, frozen=True)
class OrcaMessageConfig:
    """Configuration for sending an inter-agent message or settlement signal (Rule 12)."""

    subject: str
    to: str | None = None  # "run:<id>", "dispatch:<id>", "@all", None (defaults to Run)
    body: str | None = None
    message_type: str = (
        "status"  # "status", "dispatch", "worker_done", "question", "heartbeat"
    )
    task_id: str | None = None
    dispatch_id: str | None = None
    outcome: str | None = None  # "succeeded", "failed" (required for worker_done)
    files_modified: str | None = None
    report_path: str | None = None

    def __post_init__(self) -> None:
        assert self.subject and len(self.subject.strip()) > 0, (
            "Message subject must be non-empty"
        )
        if self.message_type == "worker_done":
            assert self.outcome in ("succeeded", "failed"), (
                "worker_done message requires outcome 'succeeded' or 'failed'"
            )


@dataclass(slots=True, frozen=True)
class OrcaDeliveryBatch:
    """Record returned when querying the coordinator FIFO mailbox (Rule 12)."""

    delivery_id: str
    messages: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    satisfied: bool = True
    has_keepalive: bool = False

    def __post_init__(self) -> None:
        assert self.delivery_id and len(self.delivery_id.strip()) > 0, (
            "Delivery ID must be non-empty"
        )


@dataclass(slots=True, frozen=True)
class OrcaMailboxMessage:
    """Slotted immutable record representing an incoming message in the FIFO inbox (Rule 12)."""

    id: str
    subject: str
    sender: str | None = None
    to: str | None = None
    body: str | None = None
    message_type: str = "status"
    task_id: str | None = None
    dispatch_id: str | None = None
    outcome: str | None = None
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        assert self.id and len(self.id.strip()) > 0, "Message ID must be non-empty"
        assert self.subject and len(self.subject.strip()) > 0, (
            "Message subject must be non-empty"
        )


@dataclass(slots=True, frozen=True)
class OrcaTaskSettlement:
    """Slotted immutable settlement report returned upon task completion (Rule 12)."""

    task_id: str
    dispatch_id: str
    outcome: str  # "succeeded" or "failed"
    worktree_id: str
    files_modified: tuple[str, ...] = field(default_factory=tuple)
    report: str = ""
    elapsed_seconds: float = 0.0
    status: str = "settled"

    def __post_init__(self) -> None:
        assert self.task_id and len(self.task_id.strip()) > 0, (
            "Task ID must be non-empty"
        )
        assert self.dispatch_id and len(self.dispatch_id.strip()) > 0, (
            "Dispatch ID must be non-empty"
        )
        assert self.outcome in ("succeeded", "failed"), (
            f"Outcome must be 'succeeded' or 'failed', got '{self.outcome}'"
        )


@runtime_checkable
class OrcaBridgeService(Protocol):
    """Protocol for Orca worktree management, multi-agent worker dispatching, and FIFO coordinator inboxes."""

    def create_worktree(self, config: OrcaWorktreeConfig) -> OrcaWorktreeInfo:
        """Create or provision an isolated Git worktree for an autonomous agent."""
        ...

    def list_worktrees(self, repo_id: str | None = None) -> list[OrcaWorktreeInfo]:
        """List active and detected Git worktrees across repositories."""
        ...

    def create_run(self, config: OrcaRunConfig) -> OrcaRunInfo:
        """Create and bind an orchestration coordinator Run namespace and FIFO inbox."""
        ...

    def start_worker(self, config: OrcaWorkerConfig) -> OrcaWorkerDispatchReceipt:
        """Start a supervised agent worker in a dedicated worktree with injected authority."""
        ...

    def check_mailbox(
        self,
        terminal: str | None = None,
        wait: bool = False,
        timeout_ms: int = 15000,
        types: str | None = None,
        ack_delivery_id: str | None = None,
    ) -> OrcaDeliveryBatch:
        """Query or await the FIFO coordinator mailbox for incoming agent reports."""
        ...

    def send_message(self, config: OrcaMessageConfig) -> dict[str, Any]:
        """Send an inter-agent message or post a worker settlement signal."""
        ...

    def send_terminal_input(
        self, terminal: str, text: str, enter: bool = True
    ) -> dict[str, Any]:
        """Deliver input directly to an active agent terminal PTY."""
        ...

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
        ...


ORCA_BRIDGE_KEY: ServiceKey[OrcaBridgeService] = ServiceKey("service.orca_bridge")
