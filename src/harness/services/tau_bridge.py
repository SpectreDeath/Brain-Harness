"""TauBridge service protocol, typed models, domain engines, and ServiceKey.

Elevates Pi-style minimalist coding agent harness mechanics (branchable session tree DAGs,
locked append-only JSONL storage, provider-safe in-flight tool history repair, and project-trust security gating)
into a first-class micro-kernel IoC service seam. Grounded in Tau (v0.4.4, huggingface/tau) and Pi architecture.

Rule 12: Slotted & frozen dataclass architecture.
Rule 21: In-flight tool-call stream normalization & promotion.
Rule 23: Windows UTF-8 stream codec entrypoint invariant.
Rule 45 & Rule 49: Skill-to-IoC micro-kernel seam elevation.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import sys
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import structlog
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey

logger = structlog.get_logger(__name__)

# Rule 23: Windows UTF-8 stream codec entrypoint invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Cross-platform advisory file locking imports
_HAS_FCNTL = False
_HAS_MSVCRT = False

try:
    import fcntl

    _HAS_FCNTL = True
except ImportError:
    pass

try:
    import msvcrt

    _HAS_MSVCRT = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Slotted & Frozen Domain Models (Rule 12)
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class SessionNode:
    """Immutable session tree entry node forming the conversation DAG."""

    id: str
    parent_id: str | None = None
    type: str = "message"
    role: str = "user"
    content: str = ""
    tool_calls: tuple[dict[str, Any], ...] = ()
    tool_call_id: str | None = None
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("SessionNode id cannot be empty.")
        if self.parent_id == self.id:
            raise ValueError("SessionNode parent_id cannot reference itself (cycle).")

    def to_dict(self) -> dict[str, Any]:
        """Convert immutable node to dictionary."""
        d: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "role": self.role,
            "content": self.content,
        }
        if self.parent_id is not None:
            d["parent_id"] = self.parent_id
        if self.tool_calls:
            d["tool_calls"] = list(self.tool_calls)
        if self.tool_call_id is not None:
            d["tool_call_id"] = self.tool_call_id
        if self.timestamp:
            d["timestamp"] = self.timestamp
        return d


@dataclass(slots=True, frozen=True)
class BranchPath:
    """Resolved linear conversation ancestry from root to target entry."""

    target_id: str
    path_entries: tuple[SessionNode, ...]
    depth: int
    total_entries: int
    branch_count: int

    def __post_init__(self) -> None:
        if self.depth < 0:
            raise ValueError("BranchPath depth cannot be negative.")


@dataclass(slots=True, frozen=True)
class ToolCallRecord:
    """Normalized tool call reference."""

    call_id: str
    tool_name: str
    arguments: str = "{}"

    def __post_init__(self) -> None:
        if not self.call_id:
            raise ValueError("ToolCallRecord call_id cannot be empty.")


@dataclass(slots=True, frozen=True)
class HistoryRepairResult:
    """Immutable result of provider-safe tool history normalization."""

    repaired_messages: tuple[dict[str, Any], ...]
    dropped_count: int
    synthesized_count: int
    repairs_applied: tuple[str, ...]
    is_modified: bool

    def __post_init__(self) -> None:
        if self.dropped_count < 0 or self.synthesized_count < 0:
            raise ValueError("Drop and synthesis counts must be non-negative.")


@dataclass(slots=True, frozen=True)
class TrustScope:
    """Workspace boundary trust and security analysis."""

    project_path: str
    is_trusted: bool
    git_root: str | None
    protected_assets: tuple[str, ...]
    warnings: tuple[str, ...]
    permission_level: str

    def __post_init__(self) -> None:
        if self.permission_level not in {"TRUSTED", "RESTRICTED", "BLOCKED"}:
            raise ValueError(f"Invalid permission level: {self.permission_level}")


@dataclass(slots=True, frozen=True)
class JournalEntryRecord:
    """Immutable record of an append-only locked journal entry."""

    journal_path: str
    entry_id: str
    byte_offset: int
    timestamp: str

    def __post_init__(self) -> None:
        if self.byte_offset < 0:
            raise ValueError("byte_offset cannot be negative.")


# ---------------------------------------------------------------------------
# Cross-Platform Advisory File Locking & Append-Only Journal Manager
# ---------------------------------------------------------------------------


class SessionJournalManager:
    """Manages append-only JSONL session journals with advisory file locking."""

    @classmethod
    @contextlib.contextmanager
    def locked_file(cls, path: Path, mode: str) -> Generator[Any, None, None]:
        """Context manager providing non-blocking advisory file locking."""
        path.parent.mkdir(parents=True, exist_ok=True)
        f = open(path, mode, encoding="utf-8")  # noqa: SIM115
        locked = False
        try:
            if _HAS_FCNTL:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    locked = True
                except (BlockingIOError, OSError):
                    # Advisory fallback: lock contention or non-supported FS
                    pass
            elif _HAS_MSVCRT:
                try:
                    # Lock first byte non-blocking
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    locked = True
                except OSError:
                    pass
            yield f
        finally:
            if locked:
                try:
                    if _HAS_FCNTL:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    elif _HAS_MSVCRT:
                        f.seek(0)
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                except Exception:
                    pass
            f.close()

    @classmethod
    def append_entry(
        cls, journal_path: str | Path, entry: SessionNode | dict[str, Any]
    ) -> SessionNode:
        """Atomically append a session entry to the locked JSONL journal."""
        p = Path(journal_path)
        node = (
            entry
            if isinstance(entry, SessionNode)
            else SessionTreeResolver.parse_entry(entry)
        )
        if not node.timestamp:
            ts = datetime.now(timezone.utc).isoformat()
            node = SessionNode(
                id=node.id,
                parent_id=node.parent_id,
                type=node.type,
                role=node.role,
                content=node.content,
                tool_calls=node.tool_calls,
                tool_call_id=node.tool_call_id,
                timestamp=ts,
            )

        line = json.dumps(node.to_dict(), ensure_ascii=False) + "\n"
        with cls.locked_file(p, "a") as f:
            f.write(line)
            f.flush()

        return node

    @classmethod
    def load_entries(cls, journal_path: str | Path) -> list[SessionNode]:
        """Read all session entries from an append-only JSONL journal."""
        p = Path(journal_path)
        if not p.exists():
            return []

        entries: list[SessionNode] = []
        with cls.locked_file(p, "r") as f:
            for line_idx, line in enumerate(f, start=1):
                raw = line.strip()
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                    node = SessionTreeResolver.parse_entry(data)
                    entries.append(node)
                except Exception as exc:
                    logger.warning(
                        "corrupt_journal_line_skipped",
                        line_idx=line_idx,
                        journal=str(p),
                        error=str(exc),
                    )
        return entries


# ---------------------------------------------------------------------------
# Deepened Session Tree Resolver (Ancestry, Leaves, Fork Points, ASCII Tree)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Deepened Tool History Repair Engine (Rule 21 Normalization & Auto-Repair)
# ---------------------------------------------------------------------------


class ToolHistoryRepairEngine:
    """Normalizes message history to guarantee provider tool-call and tool-result parity.

    Prevents 400 Bad Request provider crashes. Auto-repairs argument JSON syntax (trailing commas,
    markdown fences) per Rule 21 and drops orphan tool responses.
    """

    @classmethod
    def sanitize_arguments_json(cls, raw_args: Any) -> str:
        """Auto-repair JSON arguments string (trailing commas, markdown fences) per Rule 21."""
        if isinstance(raw_args, dict):
            return json.dumps(raw_args)
        if not isinstance(raw_args, str) or not raw_args.strip():
            return "{}"

        text = raw_args.strip()
        # Strip markdown code fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()

        # Try parsing directly
        try:
            parsed = json.loads(text)
            return json.dumps(parsed)
        except Exception:
            pass

        # Auto-repair trailing commas
        cleaned = re.sub(r",\s*([\]}])", r"\1", text)
        try:
            parsed = json.loads(cleaned)
            return json.dumps(parsed)
        except Exception:
            # Fall back to cleaned string
            return cleaned

    @classmethod
    def repair(cls, messages: list[dict[str, Any]]) -> HistoryRepairResult:
        """Execute deterministic multi-pass tool history repair."""
        repaired: list[dict[str, Any]] = []
        repairs_applied: list[str] = []
        dropped_count = 0
        synthesized_count = 0

        # Build index of all declared tool calls in the transcript
        all_call_ids: set[str] = set()
        for msg in messages:
            if msg.get("role") == "assistant":
                for call in msg.get("tool_calls") or []:
                    cid = call.get("id")
                    if cid:
                        all_call_ids.add(cid)

        i = 0
        n = len(messages)

        while i < n:
            msg = messages[i]
            role = msg.get("role")

            if role == "tool":
                t_id = msg.get("tool_call_id")
                # Drop orphan tool response if call ID was never declared
                if not t_id or t_id not in all_call_ids:
                    dropped_count += 1
                    repairs_applied.append(
                        f"Dropped orphan tool response message with tool_call_id '{t_id}'"
                    )
                    i += 1
                    continue

                repaired.append(dict(msg))
                i += 1
                continue

            if role == "assistant" and msg.get("tool_calls"):
                repaired_msg = dict(msg)
                cleaned_calls: list[dict[str, Any]] = []
                for call in msg.get("tool_calls") or []:
                    c_dict = dict(call)
                    fn = c_dict.get("function")
                    if isinstance(fn, dict) and "arguments" in fn:
                        repaired_args = cls.sanitize_arguments_json(fn["arguments"])
                        if repaired_args != fn["arguments"]:
                            fn["arguments"] = repaired_args
                            repairs_applied.append(
                                f"Repaired tool arguments JSON for call '{c_dict.get('id')}'"
                            )
                        c_dict["function"] = fn
                    cleaned_calls.append(c_dict)

                repaired_msg["tool_calls"] = cleaned_calls
                repaired.append(repaired_msg)

                call_ids = [c.get("id") for c in cleaned_calls if c.get("id")]

                # Inspect subsequent tool messages following this assistant message
                j = i + 1
                received_tool_ids: set[str] = set()
                while j < n and messages[j].get("role") == "tool":
                    cand_id = messages[j].get("tool_call_id")
                    if cand_id in call_ids:
                        received_tool_ids.add(cand_id)
                        repaired.append(dict(messages[j]))
                    elif cand_id in all_call_ids:
                        # Belongs to another call block; preserve it
                        repaired.append(dict(messages[j]))
                    else:
                        # Orphan tool message
                        dropped_count += 1
                        repairs_applied.append(
                            f"Dropped unmatched tool message with id '{cand_id}'"
                        )
                    j += 1

                # Synthesize placeholders for any missing tool calls in this block
                for cid in call_ids:
                    if cid not in received_tool_ids:
                        synthesized_count += 1
                        synth_msg = {
                            "role": "tool",
                            "tool_call_id": cid,
                            "content": "[Notice: Tool execution was interrupted or missing in transcript]",
                        }
                        repaired.append(synth_msg)
                        repairs_applied.append(
                            f"Synthesized placeholder response for unresponded tool_call '{cid}'"
                        )

                i = j
                continue

            # Standard message (user, system, or assistant without tool_calls)
            repaired.append(dict(msg))
            i += 1

        is_modified = (
            dropped_count > 0 or synthesized_count > 0 or len(repairs_applied) > 0
        )

        return HistoryRepairResult(
            repaired_messages=tuple(repaired),
            dropped_count=dropped_count,
            synthesized_count=synthesized_count,
            repairs_applied=tuple(repairs_applied),
            is_modified=is_modified,
        )


# ---------------------------------------------------------------------------
# Deepened Project Trust Evaluator (Path Confinement & Depth-2 Scans)
# ---------------------------------------------------------------------------


class ProjectTrustEvaluator:
    """Evaluates workspace boundaries, detects Git roots, and verifies path confinement."""

    DEFAULT_SENSITIVE_PATTERNS = (
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "credentials.json",
        "service_account.json",
        "id_rsa",
        "id_ed25519",
        ".git/config",
    )

    SENSITIVE_DIRS = (
        ".secrets",
        ".aws",
        ".ssh",
    )

    @classmethod
    def is_path_confined(
        cls, target_path: str | Path, root_path: str | Path
    ) -> bool:
        """Verify target path does not escape root path via directory traversal."""
        try:
            r = Path(root_path).resolve()
            t = Path(target_path).resolve()
            return t == r or r in t.parents
        except Exception:
            return False

    @classmethod
    def evaluate(
        cls,
        project_path: str,
        trusted_roots: list[str] | None = None,
        custom_sensitive_patterns: tuple[str, ...] | None = None,
    ) -> TrustScope:
        """Evaluate project security posture, directory traversal, and sensitive assets."""
        try:
            p = Path(project_path).resolve()
        except Exception:
            p = Path(os.path.abspath(project_path))

        warnings: list[str] = []
        git_root: str | None = None

        # Search for .git root by traversing up
        curr = p
        while curr != curr.parent:
            if (curr / ".git").is_dir():
                git_root = str(curr)
                break
            curr = curr.parent

        if git_root is None:
            warnings.append(
                "Project is not contained inside a recognized Git repository."
            )

        patterns = custom_sensitive_patterns or cls.DEFAULT_SENSITIVE_PATTERNS
        detected_sensitive: list[str] = []

        if p.exists() and p.is_dir():
            # Depth 1 check
            for pat in patterns:
                target = p / pat
                if target.exists():
                    detected_sensitive.append(pat)

            # Depth 2 check for sensitive directories
            for sdir in cls.SENSITIVE_DIRS:
                target_dir = p / sdir
                if target_dir.exists() and target_dir.is_dir():
                    detected_sensitive.append(f"{sdir}/")

        # Trust evaluation
        is_trusted = False
        if trusted_roots:
            for tr in trusted_roots:
                if cls.is_path_confined(p, tr):
                    is_trusted = True
                    break
        else:
            # Default heuristic: Git root exists and no private keys
            has_private_keys = any(
                s in detected_sensitive for s in ("id_rsa", "id_ed25519")
            )
            is_trusted = (git_root is not None) and not has_private_keys

        if detected_sensitive:
            warnings.append(
                f"Detected sensitive assets in project: {', '.join(detected_sensitive)}"
            )

        permission_level = "TRUSTED" if is_trusted else "RESTRICTED"
        if any(s in detected_sensitive for s in ("id_rsa", "id_ed25519")):
            permission_level = "BLOCKED"
            warnings.append(
                "Sensitive SSH private keys detected. Workspace execution blocked."
            )

        return TrustScope(
            project_path=str(p),
            is_trusted=is_trusted and permission_level != "BLOCKED",
            git_root=git_root,
            protected_assets=tuple(detected_sensitive),
            warnings=tuple(warnings),
            permission_level=permission_level,
        )


# ---------------------------------------------------------------------------
# Slotted & Delegating PiHarnessEngine (Rule 12 & Rule 49)
# ---------------------------------------------------------------------------


class PiHarnessEngine:
    """Unified coordinator for Pi-style coding agent harness operations."""

    def __init__(self) -> None:
        self.tree_resolver = SessionTreeResolver()
        self.history_repair = ToolHistoryRepairEngine()
        self.trust_evaluator = ProjectTrustEvaluator()
        self.journal_manager = SessionJournalManager()

    def resolve_session_path(
        self, entries: list[dict[str, Any] | SessionNode], target_id: str
    ) -> BranchPath:
        return self.tree_resolver.resolve_path(entries, target_id)

    def find_branch_leaves(
        self, entries: list[dict[str, Any] | SessionNode]
    ) -> list[SessionNode]:
        return self.tree_resolver.find_leaves(entries)

    def find_fork_points(
        self, entries: list[dict[str, Any] | SessionNode]
    ) -> dict[str, list[str]]:
        return self.tree_resolver.find_fork_points(entries)

    def render_session_tree(
        self,
        entries: list[dict[str, Any] | SessionNode],
        root_id: str | None = None,
    ) -> str:
        return self.tree_resolver.render_ascii_tree(entries, root_id=root_id)

    def repair_tool_history(
        self, messages: list[dict[str, Any]]
    ) -> HistoryRepairResult:
        return self.history_repair.repair(messages)

    def evaluate_project_trust(
        self, project_path: str, trusted_roots: list[str] | None = None
    ) -> TrustScope:
        return self.trust_evaluator.evaluate(project_path, trusted_roots)

    def is_path_confined(
        self, target_path: str | Path, root_path: str | Path
    ) -> bool:
        return self.trust_evaluator.is_path_confined(target_path, root_path)

    def append_journal_entry(
        self, journal_path: str | Path, entry: SessionNode | dict[str, Any]
    ) -> SessionNode:
        return self.journal_manager.append_entry(journal_path, entry)

    def load_journal_entries(
        self, journal_path: str | Path
    ) -> list[SessionNode]:
        return self.journal_manager.load_entries(journal_path)

    @staticmethod
    def format_rpc_envelope(
        request_id: str | int | None,
        result: Any = None,
        error: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Format Pi-compatible JSON-RPC envelope."""
        env: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
        if error is not None:
            env["error"] = error
        else:
            env["result"] = result
        return env


# ---------------------------------------------------------------------------
# Pydantic DTOs & Micro-Kernel IoC Service Protocol (Rule 45 & Rule 49)
# ---------------------------------------------------------------------------


class SessionPathResult(BaseModel):
    """Payload representing linear ancestry traversal from root to a target branch entry."""

    target_id: str = Field(..., description="ID of the resolved target entry")
    path_entries: list[dict[str, Any]] = Field(
        default_factory=list, description="Ordered linear entries from root to target"
    )
    depth: int = Field(..., description="Number of entries in the linear ancestry path")
    total_tree_entries: int = Field(
        ..., description="Total entries present in the session graph"
    )
    branch_count: int = Field(
        ..., description="Number of branch points detected across the tree"
    )


class HistoryRepairReport(BaseModel):
    """Payload representing in-flight provider-safe tool history normalization."""

    repaired_messages: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Cleaned, provider-safe message list ready for model invocation",
    )
    dropped_count: int = Field(
        default=0, description="Number of orphan or malformed tool messages dropped"
    )
    synthesized_count: int = Field(
        default=0,
        description="Number of placeholder tool results synthesized for unresponded calls",
    )
    repairs_applied: list[str] = Field(
        default_factory=list, description="Human-readable log of specific repairs made"
    )
    is_modified: bool = Field(
        ..., description="Whether message history required modification"
    )


class ProjectTrustEvaluation(BaseModel):
    """Payload representing workspace boundary trust evaluation."""

    project_path: str = Field(..., description="Target project canonical path")
    is_trusted: bool = Field(
        ..., description="Whether target project is within trusted scope"
    )
    git_root: str | None = Field(
        default=None, description="Discovered Git root directory if present"
    )
    protected_assets: list[str] = Field(
        default_factory=list,
        description="Detected sensitive/protected files (.env, credentials, etc.)",
    )
    warnings: list[str] = Field(
        default_factory=list, description="Security and permission warnings"
    )
    permission_level: str = Field(
        ..., description="Permission tier: TRUSTED | RESTRICTED | BLOCKED"
    )


class RpcProtocolEnvelope(BaseModel):
    """Payload representing a Pi-compatible JSONL RPC response envelope."""

    jsonrpc: str = Field(default="2.0", description="RPC protocol version")
    id: str | int | None = Field(..., description="Request identifier")
    result: Any = Field(default=None, description="Success payload if applicable")
    error: dict[str, Any] | None = Field(
        default=None, description="Error payload if applicable"
    )


@runtime_checkable
class TauBridgeService(Protocol):
    """Protocol for Pi-style coding agent harness operations."""

    def resolve_session_path(
        self, entries: list[dict[str, Any]], target_entry_id: str
    ) -> SessionPathResult:
        """Resolve linear conversation ancestry from root to a target branch entry."""
        ...

    def repair_tool_history(
        self, messages: list[dict[str, Any]]
    ) -> HistoryRepairReport:
        """Normalize message history to guarantee provider tool-call and tool-result parity."""
        ...

    def evaluate_project_trust(
        self, project_path: str, trusted_roots: list[str] | None = None
    ) -> ProjectTrustEvaluation:
        """Evaluate workspace trust boundaries, git root inheritance, and protected resources."""
        ...

    def format_rpc_envelope(
        self,
        request_id: str | int | None,
        result: Any = None,
        error: dict[str, Any] | None = None,
    ) -> RpcProtocolEnvelope:
        """Format a Pi-compatible JSONL RPC message envelope."""
        ...

    def append_journal_entry(
        self, journal_path: str | Path, entry: dict[str, Any] | SessionNode
    ) -> dict[str, Any]:
        """Atomically append a session node to an advisory locked JSONL journal."""
        ...

    def load_journal_entries(
        self, journal_path: str | Path
    ) -> list[dict[str, Any]]:
        """Load session entries from an append-only JSONL journal."""
        ...

    def render_session_tree(
        self, entries: list[dict[str, Any]], root_id: str | None = None
    ) -> str:
        """Render deterministic ASCII DAG tree representation."""
        ...

    def find_branch_leaves(
        self, entries: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Find active branch tips / leaf nodes in a session tree."""
        ...

    def is_path_confined(
        self, target_path: str | Path, root_path: str | Path
    ) -> bool:
        """Verify target path does not escape root path via directory traversal."""
        ...


class DefaultTauHarnessBridgeService(TauBridgeService):
    """Default authoritative implementation of TauBridgeService."""

    def __init__(self) -> None:
        self._engine = PiHarnessEngine()

    def resolve_session_path(
        self, entries: list[dict[str, Any]], target_entry_id: str
    ) -> SessionPathResult:
        """Resolve linear conversation ancestry from root to a target branch entry."""
        res = self._engine.resolve_session_path(entries, target_entry_id)
        return SessionPathResult(
            target_id=res.target_id,
            path_entries=[node.to_dict() for node in res.path_entries],
            depth=res.depth,
            total_tree_entries=res.total_entries,
            branch_count=res.branch_count,
        )

    def repair_tool_history(
        self, messages: list[dict[str, Any]]
    ) -> HistoryRepairReport:
        """Normalize message history to guarantee provider tool-call and tool-result parity."""
        res = self._engine.repair_tool_history(messages)
        return HistoryRepairReport(
            repaired_messages=list(res.repaired_messages),
            dropped_count=res.dropped_count,
            synthesized_count=res.synthesized_count,
            repairs_applied=list(res.repairs_applied),
            is_modified=res.is_modified,
        )

    def evaluate_project_trust(
        self, project_path: str, trusted_roots: list[str] | None = None
    ) -> ProjectTrustEvaluation:
        """Evaluate workspace trust boundaries, git root inheritance, and protected resources."""
        res = self._engine.evaluate_project_trust(project_path, trusted_roots)
        return ProjectTrustEvaluation(
            project_path=res.project_path,
            is_trusted=res.is_trusted,
            git_root=res.git_root,
            protected_assets=list(res.protected_assets),
            warnings=list(res.warnings),
            permission_level=res.permission_level,
        )

    def format_rpc_envelope(
        self,
        request_id: str | int | None,
        result: Any = None,
        error: dict[str, Any] | None = None,
    ) -> RpcProtocolEnvelope:
        """Format a Pi-compatible JSONL RPC message envelope."""
        env = self._engine.format_rpc_envelope(request_id, result=result, error=error)
        return RpcProtocolEnvelope(
            jsonrpc=env["jsonrpc"],
            id=env["id"],
            result=env.get("result"),
            error=env.get("error"),
        )

    def append_journal_entry(
        self, journal_path: str | Path, entry: dict[str, Any] | SessionNode
    ) -> dict[str, Any]:
        """Atomically append a session node to an advisory locked JSONL journal."""
        node = self._engine.append_journal_entry(journal_path, entry)
        return node.to_dict()

    def load_journal_entries(
        self, journal_path: str | Path
    ) -> list[dict[str, Any]]:
        """Load session entries from an append-only JSONL journal."""
        nodes = self._engine.load_journal_entries(journal_path)
        return [node.to_dict() for node in nodes]

    def render_session_tree(
        self, entries: list[dict[str, Any]], root_id: str | None = None
    ) -> str:
        """Render deterministic ASCII DAG tree representation."""
        return self._engine.render_session_tree(entries, root_id=root_id)

    def find_branch_leaves(
        self, entries: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Find active branch tips / leaf nodes in a session tree."""
        nodes = self._engine.find_branch_leaves(entries)
        return [node.to_dict() for node in nodes]

    def is_path_confined(
        self, target_path: str | Path, root_path: str | Path
    ) -> bool:
        """Verify target path does not escape root path via directory traversal."""
        return self._engine.is_path_confined(target_path, root_path)


TAU_HARNESS_BRIDGE_SERVICE_KEY: ServiceKey[TauBridgeService] = ServiceKey(
    "service.tau_harness_bridge"
)
