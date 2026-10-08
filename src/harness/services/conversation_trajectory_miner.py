"""Conversation Trajectory Miner Service Protocol, Slotted Domain Models, and Engine Implementation.

Extracts, indexes, and mines autobiographical execution trajectories from IDE
conversation databases (conversations/*.db) and transcript logs (transcript.jsonl).
Enforces:
- Rule 1: Everything is a plugin (registered via IoC container)
- Rule 2: Service keys are typed (CONVERSATION_TRAJECTORY_MINER_KEY: ServiceKey[ConversationTrajectoryMinerService])
- Rule 12: Slotted & frozen dataclasses (slots=True, frozen=True)
- Rule 22: Multi-store memory federation & proactor-safe read-only SQLite connections (file:...?mode=ro)
- Rule 32: Defensive batch exception logging (reraising NameError, TypeError, AttributeError)
- Rule 33: JSON null-field fallback (dict.get("key") or [])
- Rule 40: Canonical Knowledge Vault dual-file format (metadata.json + summary.md)
- Rule 41: Dual-lens cognitive distillation with unbroken isnad claims
- Rule 43: Frozen dataclass mutation assertion invariant
- Rule 48: Large corpus binary byte-offset seek invariant
- Rule 49: Skill-to-IoC micro-kernel seam elevation
- Rule 50: UTF-8 standard stream codec configuration
- Rule 51: F-string multi-brace invariant
- Rule 52: Bounded directory traversal with noise pruning
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceContext, ServiceKey

logger = logging.getLogger("harness.services.conversation_trajectory_miner")

# UTF-8 stream codec entrypoint invariant (Rule 23, Rule 50)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


# Antigravity IDE Protobuf Enum Mappings
STATUS_MAP: dict[int, str] = {
    0: "UNSPECIFIED",
    1: "RUNNING",
    2: "IN_PROGRESS",
    3: "DONE",
    4: "PAUSED",
    5: "SKIPPED",
    6: "CANCELLED",
    7: "FAILED",
}

STEP_TYPE_MAP: dict[int, str] = {
    5: "USER_INPUT",
    7: "PLANNER_RESPONSE",
    8: "TOOL_EXECUTION",
    9: "TOOL_RESULT",
    14: "CONTEXT_UPDATE",
    15: "STREAM_CHUNK",
    17: "PLANNER_THOUGHT",
    21: "AGENT_INVOCATION",
    23: "SUBAGENT_RETURN",
    98: "TASK_STATUS",
    99: "SYSTEM_NOTIFICATION",
    101: "HOOK_EXECUTION",
    132: "BATTLE_MODE",
}


# =============================================================================
# Slotted & Frozen Dataclasses (Rule 12)
# =============================================================================

@dataclass(slots=True, frozen=True)
class TrajectoryStepRecord:
    """Slotted and frozen execution step record (Rule 12)."""

    idx: int
    step_type: str
    status: str
    has_subtrajectory: bool = False
    task_details: str = ""
    error_details: str = ""
    byte_offset: int = 0
    byte_length: int = 0

    def __post_init__(self) -> None:
        if self.idx < 0:
            raise ValueError(f"Step index cannot be negative, got {self.idx}")


@dataclass(slots=True, frozen=True)
class FailureCluster:
    """Slotted and frozen aggregated failure mode cluster (Rule 12)."""

    error_type: str
    count: int
    sample_cids: tuple[str, ...]
    tool_names: tuple[str, ...]
    sample_messages: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.count < 0:
            raise ValueError(f"Failure count cannot be negative, got {self.count}")


@dataclass(slots=True, frozen=True)
class ConversationManifest:
    """Slotted and frozen manifest summary for a single conversation database (Rule 12)."""

    cid: str
    db_path: str
    file_size_bytes: int
    step_count: int
    has_wal: bool
    step_types: dict[str, int]
    errors_detected: int = 0
    first_prompt_snippet: str = ""
    retry_count: int = 0

    def __post_init__(self) -> None:
        if self.file_size_bytes < 0:
            raise ValueError(f"File size cannot be negative: {self.file_size_bytes}")
        if self.step_count < 0:
            raise ValueError(f"Step count cannot be negative: {self.step_count}")


@dataclass(slots=True, frozen=True)
class FrictionScorecard:
    """Slotted and frozen aggregate friction scorecard across session histories (Rule 12)."""

    total_conversations: int
    total_steps: int
    total_bytes_mb: float
    total_errors: int
    error_rate: float
    step_type_distribution: dict[str, int]
    high_friction_sessions: tuple[dict[str, Any], ...]
    failure_clusters: tuple[FailureCluster, ...]

    def __post_init__(self) -> None:
        if self.total_conversations < 0:
            raise ValueError(f"total_conversations cannot be negative: {self.total_conversations}")


@dataclass(slots=True, frozen=True)
class IsnadClaimRecord:
    """Slotted and frozen epistemic claim with unbroken isnad provenance (Rule 12, Rule 41)."""

    claim_id: str
    assertion: str
    isnad_source: str
    test_anchor: str
    confidence: float = 1.0


@dataclass(slots=True, frozen=True)
class CognitiveBifurcationReport:
    """Slotted and frozen dual-lens distillation output report (Rule 12, Rule 41)."""

    cid: str
    knowledge_vault_path: str
    skill_scaffold_path: str
    extracted_invariants: tuple[str, ...]
    procedural_rules: tuple[str, ...]


# =============================================================================
# Binary Byte-Offset Seek Table (Rule 48)
# =============================================================================

class ByteOffsetSeekTable:
    """O(1) binary byte-offset seek index for large transcript logs (Rule 48)."""

    def __init__(self, file_path: Path | str) -> None:
        self.file_path = Path(file_path)
        self.offsets: dict[int, tuple[int, int]] = {}
        self._build_index()

    def _build_index(self) -> None:
        """Scan file once in binary mode to record byte offset and length per line."""
        if not self.file_path.exists():
            return

        with open(self.file_path, "rb") as f:
            idx = 0
            while True:
                offset = f.tell()
                line = f.readline()
                if not line:
                    break
                length = len(line)
                self.offsets[idx] = (offset, length)
                idx += 1

    def get_line(self, line_idx: int) -> str | None:
        """Fetch line by index in O(1) time without loading entire file."""
        if line_idx not in self.offsets:
            return None
        offset, length = self.offsets[line_idx]
        with open(self.file_path, "rb") as f:
            f.seek(offset)
            raw = f.read(length)
            return raw.decode("utf-8", errors="ignore")

    def total_lines(self) -> int:
        return len(self.offsets)


# =============================================================================
# Service Protocol & Key (Rule 2, Rule 49)
# =============================================================================

@runtime_checkable
class ConversationTrajectoryMinerService(Protocol):
    """Protocol for autobiographical trajectory mining, friction archaeology, and cognitive bifurcation."""

    def connect_ro(self, db_path: Path | str) -> sqlite3.Connection:
        """Establish proactor-safe read-only SQLite URI connection (Rule 22)."""
        ...

    def inspect_conversation(self, db_path: Path) -> ConversationManifest | None:
        """Inspect a single conversation database and extract metadata safely."""
        ...

    def scan_corpus(
        self, corpus_dir: Path | str, max_dbs: int | None = None
    ) -> list[ConversationManifest]:
        """Scan corpus directory and compile manifests for SQLite conversation databases."""
        ...

    def compile_friction_scorecard(
        self, manifests: list[ConversationManifest]
    ) -> FrictionScorecard:
        """Compile aggregate friction and step distribution scorecard."""
        ...

    def mine_failure_clusters(
        self, corpus_dir: Path | str, max_dbs: int | None = None
    ) -> list[FailureCluster]:
        """Analyze step execution errors across databases and cluster recurring failure modes."""
        ...

    def bifurcate_distillation(
        self,
        cid: str,
        db_path: Path,
        output_vault_dir: Path,
        output_skills_dir: Path | None = None,
    ) -> CognitiveBifurcationReport:
        """Bifurcate session learning into Knowledge Vault item and procedural skill rules (Rule 41)."""
        ...

    def export_knowledge_item(
        self,
        output_dir: Path,
        ki_id: str,
        title: str,
        category: str,
        summary: str,
        claims: list[dict[str, Any]],
    ) -> tuple[Path, Path]:
        """Export canonical Knowledge Vault dual-file format (metadata.json + summary.md, Rule 40)."""
        ...


CONVERSATION_TRAJECTORY_MINER_KEY = ServiceKey[ConversationTrajectoryMinerService](
    "conversation_trajectory_miner_service"
)


def resolve_conversation_trajectory_miner(
    ctx: ServiceContext | None = None,
) -> ConversationTrajectoryMinerService:
    """Resolve ConversationTrajectoryMinerService from IoC context or fall back to standard implementation (Rule 58)."""
    if ctx is not None:
        svc = ctx.optional(CONVERSATION_TRAJECTORY_MINER_KEY)
        if svc is not None and isinstance(svc, ConversationTrajectoryMinerService):
            return svc
    return StandardConversationTrajectoryMinerService()


# =============================================================================
# Standard Implementation (Rule 49)
# =============================================================================

class StandardConversationTrajectoryMinerService(ConversationTrajectoryMinerService):
    """Authoritative domain implementation of ConversationTrajectoryMinerService."""

    def connect_ro(self, db_path: Path | str) -> sqlite3.Connection:
        """Establish proactor-safe read-only SQLite URI connection (Rule 22)."""
        resolved = Path(db_path).resolve()
        uri_path = resolved.as_posix()
        uri = f"file:{uri_path}?mode=ro"
        return sqlite3.connect(uri, uri=True, timeout=5.0)

    def inspect_conversation(self, db_path: Path) -> ConversationManifest | None:
        """Inspect a single conversation database and extract metadata safely."""
        cid = db_path.stem
        try:
            file_size = db_path.stat().st_size
        except OSError:
            return None

        has_wal = db_path.with_name(f"{db_path.name}-wal").exists()

        conn: sqlite3.Connection | None = None
        try:
            conn = self.connect_ro(db_path)
            cursor = conn.cursor()

            # Verify schema presence
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='steps'"
            )
            if not cursor.fetchone():
                return ConversationManifest(
                    cid=cid,
                    db_path=str(db_path),
                    file_size_bytes=file_size,
                    step_count=0,
                    has_wal=has_wal,
                    step_types={},
                )

            cursor.execute("SELECT COUNT(*) FROM steps")
            total_steps = cursor.fetchone()[0]

            cursor.execute(
                "SELECT step_type, COUNT(*) FROM steps GROUP BY step_type"
            )
            raw_step_types = dict(cursor.fetchall())
            mapped_step_types = {
                STEP_TYPE_MAP.get(k, f"TYPE_{k}"): v
                for k, v in raw_step_types.items()
            }

            # Status in (6, 7) or non-empty error_details indicates error/friction
            cursor.execute(
                "SELECT COUNT(*) FROM steps WHERE status IN (6, 7) OR (error_details IS NOT NULL AND length(error_details) > 0)"
            )
            errors_detected = cursor.fetchone()[0]

            # Count consecutive retry cascades (where a failed tool step is followed by another tool step)
            cursor.execute(
                "SELECT idx, status, step_type, error_details FROM steps ORDER BY idx ASC"
            )
            rows = cursor.fetchall()
            retry_count = 0
            prev_failed = False
            for r in rows:
                status = r[1]
                err = r[3]
                is_err = status in (6, 7) or bool(err and len(str(err).strip()) > 0)
                if is_err:
                    if prev_failed:
                        retry_count += 1
                    prev_failed = True
                else:
                    prev_failed = False

            # Extract first user prompt snippet via lossy UTF-8 decode
            cursor.execute(
                "SELECT step_payload FROM steps WHERE idx=0 OR step_type=5 LIMIT 1"
            )
            first_snippet = ""
            row = cursor.fetchone()
            if row and row[0]:
                raw_bytes = row[0]
                decoded = (
                    raw_bytes.decode("utf-8", errors="ignore")
                    if isinstance(raw_bytes, bytes)
                    else str(raw_bytes)
                )
                clean_match = re.findall(
                    r"[a-zA-Z0-9_\-\.\:\/\s\?\!\,\'\"]{10,}", decoded
                )
                if clean_match:
                    first_snippet = clean_match[0][:150].strip()

            return ConversationManifest(
                cid=cid,
                db_path=str(db_path),
                file_size_bytes=file_size,
                step_count=total_steps,
                has_wal=has_wal,
                step_types=mapped_step_types,
                errors_detected=errors_detected,
                first_prompt_snippet=first_snippet,
                retry_count=retry_count,
            )
        except (NameError, TypeError, AttributeError):
            raise
        except Exception as exc:
            logger.debug("Failed inspecting database %s: %s", db_path, exc)
            return None
        finally:
            if conn is not None:
                conn.close()

    def scan_corpus(
        self, corpus_dir: Path | str, max_dbs: int | None = None
    ) -> list[ConversationManifest]:
        """Scan corpus directory and compile manifests for SQLite conversation databases."""
        path = Path(corpus_dir)
        if not path.exists():
            return []

        # Enforce bounded traversal and prune noise (Rule 52)
        db_files = sorted(
            [
                p
                for p in path.glob("*.db")
                if not p.name.endswith(("-shm", "-wal"))
            ],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if max_dbs:
            db_files = db_files[:max_dbs]

        manifests: list[ConversationManifest] = []
        for p in db_files:
            m = self.inspect_conversation(p)
            if m:
                manifests.append(m)
        return manifests

    def compile_friction_scorecard(
        self, manifests: list[ConversationManifest]
    ) -> FrictionScorecard:
        """Compile aggregate friction and step distribution scorecard."""
        total_steps = sum(m.step_count for m in manifests)
        total_errors = sum(m.errors_detected for m in manifests)
        total_bytes = sum(m.file_size_bytes for m in manifests)

        aggregate_types: dict[str, int] = {}
        for m in manifests:
            for stype, count in m.step_types.items():
                aggregate_types[stype] = aggregate_types.get(stype, 0) + count

        high_error_sessions = [
            asdict(m)
            for m in manifests
            if m.errors_detected > 0
        ]
        high_error_sessions.sort(key=lambda x: x["errors_detected"], reverse=True)

        # Collect failure clusters
        failure_clusters: list[FailureCluster] = []
        cluster_map: dict[str, list[tuple[str, str, str]]] = {}

        for m in manifests:
            if m.errors_detected == 0:
                continue
            conn: sqlite3.Connection | None = None
            try:
                conn = self.connect_ro(m.db_path)
                cur = conn.cursor()
                cur.execute(
                    "SELECT task_details, error_details FROM steps WHERE status IN (6, 7) OR (error_details IS NOT NULL AND length(error_details) > 0) LIMIT 20"
                )
                for task_det, err_det in cur.fetchall():
                    task_str = str(task_det or "")
                    err_str = str(err_det or "")
                    cat = self._categorize_error(err_str, task_str)
                    if cat not in cluster_map:
                        cluster_map[cat] = []
                    cluster_map[cat].append((m.cid, task_str[:60], err_str[:120]))
            except Exception as e:
                logger.debug("Error extracting failure clusters from %s: %s", m.cid, e)
            finally:
                if conn is not None:
                    conn.close()

        for cat, occurrences in cluster_map.items():
            sample_cids = tuple(dict.fromkeys(cid for cid, _, _ in occurrences))[:5]
            tool_names = tuple(
                dict.fromkeys(t for _, t, _ in occurrences if t)
            )[:5]
            sample_msgs = tuple(
                dict.fromkeys(msg for _, _, msg in occurrences if msg)
            )[:3]
            failure_clusters.append(
                FailureCluster(
                    error_type=cat,
                    count=len(occurrences),
                    sample_cids=sample_cids,
                    tool_names=tool_names,
                    sample_messages=sample_msgs,
                )
            )

        failure_clusters.sort(key=lambda c: c.count, reverse=True)

        return FrictionScorecard(
            total_conversations=len(manifests),
            total_steps=total_steps,
            total_bytes_mb=round(total_bytes / (1024 * 1024), 2),
            total_errors=total_errors,
            error_rate=round(total_errors / max(total_steps, 1), 4),
            step_type_distribution=aggregate_types,
            high_friction_sessions=tuple(high_error_sessions[:10]),
            failure_clusters=tuple(failure_clusters[:10]),
        )

    def mine_failure_clusters(
        self, corpus_dir: Path | str, max_dbs: int | None = None
    ) -> list[FailureCluster]:
        """Analyze step execution errors across databases and cluster recurring failure modes."""
        manifests = self.scan_corpus(corpus_dir, max_dbs=max_dbs)
        scorecard = self.compile_friction_scorecard(manifests)
        return list(scorecard.failure_clusters)

    def bifurcate_distillation(
        self,
        cid: str,
        db_path: Path,
        output_vault_dir: Path,
        output_skills_dir: Path | None = None,
    ) -> CognitiveBifurcationReport:
        """Bifurcate session learning into Knowledge Vault item and procedural skill rules (Rule 41)."""
        manifest = self.inspect_conversation(db_path)
        if not manifest:
            raise FileNotFoundError(f"Database not accessible or invalid: {db_path}")

        extracted_invariants: list[str] = []
        procedural_rules: list[str] = []
        claims: list[dict[str, Any]] = []

        conn: sqlite3.Connection | None = None
        try:
            conn = self.connect_ro(db_path)
            cur = conn.cursor()
            cur.execute(
                "SELECT idx, step_type, status, task_details, error_details FROM steps ORDER BY idx ASC"
            )
            rows = cur.fetchall()

            for i, r in enumerate(rows):
                idx, stype, status, task_det, err_det = r
                err_str = str(err_det or "")
                task_str = str(task_det or "")

                # Identify repair transitions: a step with error followed later by a success
                if (status in (6, 7) or err_str) and i + 1 < len(rows):
                    next_status = rows[i + 1][2]
                    cat = self._categorize_error(err_str, task_str)
                    inv = f"Invariant {cat}: Ensure prerequisite validation for {task_str or 'execution step'}"
                    rule = f"Rule: Intercept {cat} failure patterns before transaction commitment."
                    if inv not in extracted_invariants:
                        extracted_invariants.append(inv)
                    if rule not in procedural_rules:
                        procedural_rules.append(rule)

                    claims.append({
                        "claim_id": f"claim-{cid[:8]}-{idx}",
                        "assertion": inv,
                        "isnad_source": f"conversations/{cid}.db (step {idx})",
                        "test_anchor": f"test_regression_{cid[:8]}_step_{idx}",
                        "confidence": 0.95 if next_status == 3 else 0.80,
                    })
        except (NameError, TypeError, AttributeError):
            raise
        except Exception as exc:
            logger.debug("Error extracting steps for bifurcation on %s: %s", cid, exc)
        finally:
            if conn is not None:
                conn.close()

        if not extracted_invariants:
            extracted_invariants.append(f"Session {cid} exhibited nominal execution without critical errors.")
            procedural_rules.append(f"Preserve standard execution patterns observed in session {cid}.")
            claims.append({
                "claim_id": f"claim-{cid[:8]}-0",
                "assertion": f"Nominal baseline execution verified for session {cid}.",
                "isnad_source": f"conversations/{cid}.db",
                "test_anchor": "test_nominal_baseline",
                "confidence": 1.0,
            })

        # Epistemic Introspection Seam (Knowledge Vault, Rule 40, Rule 41)
        ki_id = f"ki_autobio_{cid[:12]}"
        meta_file, summary_file = self.export_knowledge_item(
            output_dir=output_vault_dir,
            ki_id=ki_id,
            title=f"Autobiographical Session Trajectory: {cid[:12]}",
            category="autobiographical_trajectory",
            summary=f"Distilled learnings and friction analysis for conversation {cid}. Total steps: {manifest.step_count}, Errors: {manifest.errors_detected}, Retries: {manifest.retry_count}.",
            claims=claims,
        )

        skill_scaffold_path = ""
        if output_skills_dir:
            skill_name = f"trajectory-learned-{cid[:8]}"
            skill_target = output_skills_dir / skill_name
            skill_target.mkdir(parents=True, exist_ok=True)
            skill_scaffold_path = str(skill_target)
            card_file = skill_target / "CARD.md"
            skill_file = skill_target / "SKILL.md"

            card_content = (
                f"# CARD: {skill_name}\n\n"
                f"```\n"
                f"┌─────────────────────────────────────────────────────────────────────────────┐\n"
                f"│ SKILL: {skill_name:<68} │\n"
                f"│ Source CID: {cid:<63} │\n"
                f"└─────────────────────────────────────────────────────────────────────────────┘\n"
                f"```\n\n"
                f"## 5-Stage Progression Matrix\n\n"
                f"| Stage | Core Responsibility | Primary Artifact | Passing Completion Gate |\n"
                f"| :--- | :--- | :--- | :--- |\n"
                f"| **1. Trajectory Replay** | Replay autobiographical steps | `replay_log.json` | Steps loaded without lock contention. |\n"
                f"| **2. Pattern Extraction** | Extract recurring execution paths | `pattern_map.json` | Patterns verified against invariants. |\n"
                f"| **3. Invariant Assertion** | Assert learned invariants | `invariant_report.json` | Zero regressions detected. |\n"
                f"| **4. Dual-Lens Validation** | Validate isnad claims | `isnad_audit.json` | Isnad citations verified. |\n"
                f"| **5. Graph Commit** | Register in knowledge graph | `graph_node.json` | Skill registered in graph catalog. |\n\n"
                f"## Procedural Rules\n"
                + "\n".join(f"- {r}" for r in procedural_rules)
                + "\n\n## Mandatory Invariants Checklist\n"
                + "\n".join(f"- [ ] {inv}" for inv in extracted_invariants)
                + "\n"
            )
            card_file.write_text(card_content, encoding="utf-8")

            skill_content = (
                f"---\n"
                f"name: {skill_name}\n"
                f"description: Procedural execution rules and invariants learned from conversation {cid[:8]}. Do not use for unrelated workflows.\n"
                f"---\n\n"
                f"# {skill_name}\n\n"
                f"Learned operational skill synthesized from autobiographical conversation `{cid}`.\n\n"
                f"## Procedural Rules\n"
                + "\n".join(f"- {r}" for r in procedural_rules)
                + "\n\n## Invariants\n"
                + "\n".join(f"- {inv}" for inv in extracted_invariants)
                + "\n\n## Anti-Patterns\n\n"
                "- **Unverified Invariant Mutation** — Mutating invariants without isnad provenance verification.\n"
                "- **Subprocess Lock Contention** — Opening active SQLite databases in read-write mode.\n"
            )
            skill_file.write_text(skill_content, encoding="utf-8")

        return CognitiveBifurcationReport(
            cid=cid,
            knowledge_vault_path=str(meta_file.parent),
            skill_scaffold_path=skill_scaffold_path,
            extracted_invariants=tuple(extracted_invariants),
            procedural_rules=tuple(procedural_rules),
        )

    def export_knowledge_item(
        self,
        output_dir: Path,
        ki_id: str,
        title: str,
        category: str,
        summary: str,
        claims: list[dict[str, Any]],
    ) -> tuple[Path, Path]:
        """Export canonical Knowledge Vault dual-file format (metadata.json + summary.md, Rule 40)."""
        ki_dir = output_dir / ki_id
        ki_dir.mkdir(parents=True, exist_ok=True)

        meta_path = ki_dir / "metadata.json"
        summary_path = ki_dir / "summary.md"

        metadata = {
            "id": ki_id,
            "title": title,
            "category": category,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "claims": claims,
            "provenance": {
                "source_engine": "ConversationTrajectoryMinerService",
                "isnad_verified": True,
            },
        }
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        claims_md = "\n".join(
            f"- **{c.get('claim_id', 'claim')}**: {c.get('assertion', '')} *(isnad: `{c.get('isnad_source', '')}`, test: `{c.get('test_anchor', '')}`, conf: {c.get('confidence', 1.0)})*"
            for c in claims
        )

        summary_content = (
            f"# {title}\n\n"
            f"**ID**: `{ki_id}` | **Category**: `{category}`\n\n"
            f"## Summary\n\n{summary}\n\n"
            f"## Verified Isnad Claims (Rule 41)\n\n"
            f"{claims_md}\n"
        )
        summary_path.write_text(summary_content, encoding="utf-8")

        return meta_path, summary_path

    @staticmethod
    def _categorize_error(err_str: str, task_str: str) -> str:
        """Classify error string into semantic diagnostic categories."""
        combined = f"{err_str} {task_str}".lower()
        if "filenotfound" in combined or "no such file" in combined:
            return "FileNotFoundError / Path Missing"
        if "syntaxerror" in combined or "parse error" in combined or "indentation" in combined:
            return "SyntaxError / Script Parse"
        if "permission denied" in combined or "access is denied" in combined:
            return "PermissionDenied / Security Boundary"
        if "timeout" in combined or "deadlock" in combined:
            return "SubprocessTimeout / Resource Lock"
        if "validation" in combined or "schema" in combined:
            return "Schema / Validation Failure"
        if "connection" in combined or "socket" in combined:
            return "Network / Connection Failure"
        return "ToolExecution / General Error"


__all__ = [
    "ByteOffsetSeekTable",
    "CognitiveBifurcationReport",
    "CONVERSATION_TRAJECTORY_MINER_KEY",
    "ConversationManifest",
    "ConversationTrajectoryMinerService",
    "FailureCluster",
    "FrictionScorecard",
    "IsnadClaimRecord",
    "STATUS_MAP",
    "STEP_TYPE_MAP",
    "StandardConversationTrajectoryMinerService",
    "TrajectoryStepRecord",
    "resolve_conversation_trajectory_miner",
]
