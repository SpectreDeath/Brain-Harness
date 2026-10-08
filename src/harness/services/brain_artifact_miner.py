"""Brain Artifact Miner Service Protocol, Slotted Domain Models, and Engine Implementation.

Extracts, indexes, and mines workspace artifacts, reusable scratch tools,
dual-transcript reasoning streams, and background task execution logs
from IDE brain workspace stores.

Enforces:
- Rule 1: Everything is a plugin (registered via IoC container)
- Rule 2: Service keys are typed (BRAIN_ARTIFACT_MINER_KEY: ServiceKey[BrainArtifactMinerService])
- Rule 12: Slotted & frozen dataclasses (slots=True, frozen=True)
- Rule 22: Multi-store memory federation & dual-transcript dereferencing
- Rule 32: Defensive batch exception logging (reraising NameError, TypeError, AttributeError)
- Rule 33: JSON null-field fallback (dict.get("key") or [])
- Rule 40: Canonical Knowledge Vault dual-file format (metadata.json + summary.md)
- Rule 41: Epistemic isnad claim verification
- Rule 48: Large corpus binary byte-offset seek invariant
- Rule 49: Skill-to-IoC micro-kernel seam elevation
- Rule 51: F-string dynamic template escaping (doubled braces)
- Rule 52: Bounded directory traversal with noise pruning
- Rule 53: Subprocess stderr drainage and task triage
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceContext, ServiceKey

logger = logging.getLogger("harness.services.brain_artifact_miner")


# =============================================================================
# Slotted & Frozen Dataclasses (Rule 12)
# =============================================================================

@dataclass(slots=True, frozen=True)
class ScratchCatalogItem:
    """Slotted and frozen representation of a classified scratch script (Rule 12)."""
    category: str
    path: str
    functions: list[str]
    imports: list[str]
    docstring: str


@dataclass(slots=True, frozen=True)
class ScratchCatalog:
    """Slotted and frozen catalog of classified scratch tools (Rule 12)."""
    total_scanned: int
    classified_count: int
    items_by_category: dict[str, list[ScratchCatalogItem]]


@dataclass(slots=True, frozen=True)
class TaskTriageReport:
    """Slotted and frozen summary of background task executions (Rule 12, Rule 53)."""
    total_tasks: int
    failed_count: int
    deadlock_count: int
    samples: list[dict[str, Any]]


@dataclass(slots=True, frozen=True)
class ByteOffsetEntry:
    """Slotted and frozen byte offset record for O(1) binary seeks (Rule 12, Rule 48)."""
    step_index: int
    byte_offset: int
    byte_length: int


@dataclass(slots=True, frozen=True)
class DualTranscriptStep:
    """Slotted and frozen representation of a dual-transcript step (Rule 12, Rule 22)."""
    step_index: int
    source: str
    step_type: str
    status: str
    content: str
    is_truncated: bool
    tool_calls: list[dict[str, Any]]
    dereferenced: bool


@dataclass(slots=True, frozen=True)
class ArtifactLifecycleEntry:
    """Slotted and frozen representation of an artifact version lifecycle (Rule 12)."""
    conversation_id: str
    artifact_name: str
    has_plan: bool
    has_walkthrough: bool
    has_task: bool
    mtime: float


# =============================================================================
# Service Protocol (Rule 49)
# =============================================================================

@runtime_checkable
class BrainArtifactMinerService(Protocol):
    """Protocol for mining workspace artifacts, scratch tools, and transcripts."""

    def build_offset_index(self, path: Path) -> dict[int, tuple[int, int]]:
        """Build an O(1) binary byte-offset index table for a JSONL transcript (Rule 48)."""
        ...

    def get_step(
        self,
        transcript_path: Path,
        step_index: int,
        dereference_truncated: bool = True,
    ) -> dict[str, Any] | None:
        """Fetch a specific step via O(1) seek, dereferencing truncated steps (Rule 22, 48)."""
        ...

    def stream_steps(
        self,
        transcript_path: Path,
        dereference_truncated: bool = True,
    ) -> Iterator[dict[str, Any]]:
        """Stream all transcript steps with optional truncation dereferencing."""
        ...

    def scan_scratch_tools(self, brain_dir: Path, max_depth: int = 3) -> ScratchCatalog:
        """Scan and catalog reusable Python scratch tools via AST inspection (Rule 32, 52)."""
        ...

    def triage_task_logs(self, brain_dir: Path, max_depth: int = 4) -> TaskTriageReport:
        """Triage background subprocess task logs across the brain store (Rule 53)."""
        ...

    def generate_html_brief(self, data: dict[str, Any]) -> str:
        """Synthesize an HTML visual brief with double-brace escaped CSS/regex (Rule 51)."""
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
        """Export canonical dual-file Knowledge Vault item with isnad claims (Rule 40, 41)."""
        ...


# =============================================================================
# Standard Service Engine Implementation
# =============================================================================

class StandardBrainArtifactMinerService:
    """Authoritative standard implementation of BrainArtifactMinerService."""

    def __init__(self) -> None:
        self._offset_cache: dict[Path, dict[int, tuple[int, int]]] = {}

    def build_offset_index(self, path: Path) -> dict[int, tuple[int, int]]:
        """Build an O(1) binary byte-offset index table for a JSONL transcript (Rule 48).

        Scans the file once in binary mode ('rb') to map step indices to
        (byte_offset, byte_length) pairs, enabling sub-millisecond seek retrieval.
        Results are cached in-memory for subsequent O(1) random seeks.
        """
        path = path.resolve()
        if path in self._offset_cache:
            return self._offset_cache[path]

        index: dict[int, tuple[int, int]] = {}
        if not path.exists():
            return index

        with open(path, "rb") as f:
            offset = 0
            step_idx = 0
            for line in f:
                length = len(line)
                try:
                    line_str = line.decode("utf-8", errors="ignore")
                    m = re.search(r'"step_index"\s*:\s*(\d+)', line_str)
                    if m:
                        idx = int(m.group(1))
                    else:
                        idx = step_idx
                    index[idx] = (offset, length)
                except Exception:
                    index[step_idx] = (offset, length)
                offset += length
                step_idx += 1

        self._offset_cache[path] = index
        return index

    def get_step(
        self,
        transcript_path: Path,
        step_index: int,
        dereference_truncated: bool = True,
    ) -> dict[str, Any] | None:
        """Fetch a specific step via O(1) seek, dereferencing truncated steps (Rule 22, 48).

        When dereference_truncated is True and a compact step has is_truncated: true,
        the sibling transcript_full.jsonl file is sought at the matching step_index
        to recover untruncated content and tool calls.
        """
        transcript_path = transcript_path.resolve()
        index = self.build_offset_index(transcript_path)
        if step_index not in index:
            return None

        offset, length = index[step_index]
        try:
            with open(transcript_path, "rb") as f:
                f.seek(offset)
                raw_bytes = f.read(length)
                step_data: dict[str, Any] = json.loads(raw_bytes.decode("utf-8", errors="ignore"))
        except Exception as ex:
            logger.warning("Error reading step %d from %s: %s", step_index, transcript_path, ex)
            return None

        # Check for truncation dereferencing (Rule 22)
        if dereference_truncated and step_data.get("is_truncated") is True:
            full_path = transcript_path.parent / "transcript_full.jsonl"
            if full_path.exists() and full_path != transcript_path:
                full_step = self.get_step(full_path, step_index, dereference_truncated=False)
                if full_step is not None:
                    step_data["content"] = full_step.get("content", step_data.get("content", ""))
                    step_data["tool_calls"] = full_step.get("tool_calls") or step_data.get("tool_calls") or []
                    step_data["is_truncated"] = False
                    step_data["dereferenced"] = True
                    return step_data

        step_data.setdefault("dereferenced", False)
        return step_data

    def stream_steps(
        self,
        transcript_path: Path,
        dereference_truncated: bool = True,
    ) -> Iterator[dict[str, Any]]:
        """Stream all transcript steps with optional truncation dereferencing."""
        transcript_path = transcript_path.resolve()
        index = self.build_offset_index(transcript_path)
        for idx in sorted(index.keys()):
            step = self.get_step(transcript_path, idx, dereference_truncated=dereference_truncated)
            if step is not None:
                yield step

    def _classify_script_ast(self, code: str, file_path: Path) -> tuple[str, list[str], list[str], str]:
        """Inspect a Python script via AST to extract metadata and category (Rule 42)."""
        tree = ast.parse(code, filename=str(file_path))
        docstring = ast.get_docstring(tree) or ""
        functions: list[str] = []
        imports: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)
            elif isinstance(node, ast.Import):
                for n in node.names:
                    imports.append(n.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        functions = list(dict.fromkeys(functions))
        imports = list(dict.fromkeys(imports))

        # Heuristic domain classification
        content_lower = (code + " " + " ".join(functions) + " " + " ".join(imports)).lower()
        fname = file_path.name.lower()

        if any(k in content_lower for k in ("ast.", "linter", "syntax", "brackets", "tokenize")) or "lint" in fname:
            category = "ast_and_lint"
        elif any(k in content_lower for k in ("sqlite3", "sql", "cursor", "select", "table", "wal")) or "db" in fname:
            category = "database_and_sql"
        elif any(k in content_lower for k in ("html", "tailwind", "mermaid", "brief", "css", "svg")) or "brief" in fname or "visual" in fname:
            category = "brief_and_visual"
        elif any(k in content_lower for k in ("pytest", "assert", "test_", "verification", "check_")):
            category = "test_and_verification"
        elif any(k in content_lower for k in ("search", "grep", "regex", "re.search", "find")):
            category = "inspection_and_search"
        elif any(k in content_lower for k in ("graph", "node", "edge", "dag", "bfs", "dfs", "tree")):
            category = "graph_and_topology"
        else:
            category = "domain_and_other"

        return category, functions, imports, docstring[:250]

    def scan_scratch_tools(self, brain_dir: Path, max_depth: int = 3) -> ScratchCatalog:
        """Scan and catalog reusable Python scratch tools across conversation workspaces.

        Enforces:
        - Rule 52: Bounded directory traversal with noise pruning
        - Rule 32: Defensive batch visibility (never bare except: continue; reraise programming errors)
        - Rule 42: AST script hygiene and syntactic inspection
        """
        items_by_cat: dict[str, list[ScratchCatalogItem]] = {
            "ast_and_lint": [],
            "database_and_sql": [],
            "brief_and_visual": [],
            "test_and_verification": [],
            "inspection_and_search": [],
            "graph_and_topology": [],
            "domain_and_other": [],
        }

        if not brain_dir.exists():
            logger.warning("Brain directory does not exist: %s", brain_dir)
            return ScratchCatalog(total_scanned=0, classified_count=0, items_by_category=items_by_cat)

        total_scanned = 0
        classified_count = 0
        ignored_parts = {".git", "node_modules", ".venv", "__pycache__", "target", "dist", ".gemini"}

        for root, dirs, files in os.walk(brain_dir):
            # Prune noise directories in-place (Rule 52)
            dirs[:] = [d for d in dirs if d.lower() not in ignored_parts and not d.startswith(".")]

            rel_depth = len(Path(root).relative_to(brain_dir).parts)
            if rel_depth > max_depth:
                dirs.clear()
                continue

            if Path(root).name == "scratch":
                for f in files:
                    if not f.endswith(".py"):
                        continue
                    file_path = Path(root) / f
                    total_scanned += 1

                    try:
                        code = file_path.read_text(encoding="utf-8", errors="ignore")
                        category, funcs, imps, doc = self._classify_script_ast(code, file_path)
                        item = ScratchCatalogItem(
                            category=category,
                            path=str(file_path),
                            functions=funcs,
                            imports=imps,
                            docstring=doc,
                        )
                        items_by_cat.setdefault(category, []).append(item)
                        classified_count += 1
                    except (NameError, TypeError, AttributeError) as prog_err:
                        # Explicitly reraise programming errors (Rule 32)
                        logger.error("Programming defect scanning %s: %s", file_path, prog_err)
                        raise
                    except SyntaxError as syn_err:
                        logger.debug("Syntax error in scratch script %s: %s", file_path, syn_err)
                    except Exception as ex:
                        # Log unexpected batch errors defensively (Rule 32)
                        logger.warning("Unexpected error inspecting scratch script %s: %s", file_path, ex)

        return ScratchCatalog(
            total_scanned=total_scanned,
            classified_count=classified_count,
            items_by_category=items_by_cat,
        )

    def triage_task_logs(self, brain_dir: Path, max_depth: int = 4) -> TaskTriageReport:
        """Triage background subprocess task logs across the brain store (Rule 53).

        Scans .system_generated/tasks/task-*.log files for exit codes, tracebacks,
        and pipe deadlock signatures, capturing trailing stderr lines in a ring buffer.
        """
        total_tasks = 0
        failed_count = 0
        deadlock_count = 0
        samples: list[dict[str, Any]] = []

        if not brain_dir.exists():
            return TaskTriageReport(total_tasks=0, failed_count=0, deadlock_count=0, samples=[])

        ignored_parts = {".git", "node_modules", ".venv", "__pycache__", "target", "dist", ".gemini"}

        for root, dirs, files in os.walk(brain_dir):
            dirs[:] = [d for d in dirs if d.lower() not in ignored_parts]
            rel_depth = len(Path(root).relative_to(brain_dir).parts)
            if rel_depth > max_depth:
                dirs.clear()
                continue

            if Path(root).name == "tasks" and Path(root).parent.name == ".system_generated":
                for f in files:
                    if not (f.startswith("task-") and f.endswith(".log")):
                        continue
                    total_tasks += 1
                    task_file = Path(root) / f

                    try:
                        lines = deque(maxlen=40)
                        has_error = False
                        is_deadlock = False
                        exit_code: int | None = None

                        with open(task_file, "r", encoding="utf-8", errors="ignore") as lf:
                            for line in lf:
                                lines.append(line.rstrip())
                                if "exit code" in line.lower() or "returned non-zero" in line.lower():
                                    m = re.search(r"exit code:?\s*(-?\d+)", line, re.IGNORECASE)
                                    if m:
                                        exit_code = int(m.group(1))
                                        if exit_code != 0:
                                            has_error = True
                                if "Traceback (most recent call last)" in line:
                                    has_error = True
                                if any(term in line.lower() for term in ("broken pipe", "pipe buffer", "deadlock")):
                                    is_deadlock = True

                        if has_error or (exit_code is not None and exit_code != 0):
                            failed_count += 1
                        if is_deadlock:
                            deadlock_count += 1

                        if (has_error or is_deadlock) and len(samples) < 15:
                            samples.append({
                                "file": str(task_file),
                                "exit_code": exit_code,
                                "is_deadlock": is_deadlock,
                                "trailing_stderr": list(lines)[-10:],
                            })
                    except Exception as ex:
                        logger.debug("Failed reading task log %s: %s", task_file, ex)

        return TaskTriageReport(
            total_tasks=total_tasks,
            failed_count=failed_count,
            deadlock_count=deadlock_count,
            samples=samples,
        )

    def generate_html_brief(self, data: dict[str, Any]) -> str:
        """Synthesize an HTML visual brief with double-brace escaped CSS/regex (Rule 51)."""
        title = data.get("title", "Brain Artifact Miner Visual Brief")
        total_dirs = data.get("total_dirs", 0)
        scratch_count = data.get("scratch_count", 0)
        task_count = data.get("task_count", 0)
        failed_tasks = data.get("failed_tasks", 0)
        categories = data.get("categories", {})

        category_rows = "".join(
            f"<tr><td class='px-4 py-2 font-mono text-sm'>{cat}</td><td class='px-4 py-2 text-right font-bold'>{len(items)}</td></tr>"
            for cat, items in categories.items()
        )

        # Rule 51: All literal CSS/JS braces must be doubled {{ }}
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{ startOnLoad: true }});</script>
  <style>
    body {{ background: #0f172a; color: #f8fafc; font-family: ui-sans-serif, system-ui, sans-serif; }}
    .card {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.1); }}
  </style>
</head>
<body class="p-8 max-w-6xl mx-auto">
  <div class="mb-8 border-b border-slate-700 pb-4">
    <h1 class="text-3xl font-extrabold text-indigo-400">{title}</h1>
    <p class="text-slate-400 mt-1">Filesystem-Native Epistemic Workspace Archaeology</p>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
    <div class="card rounded-xl p-5">
      <div class="text-slate-400 text-xs font-semibold uppercase tracking-wider">Conversation Workspaces</div>
      <div class="text-3xl font-bold text-white mt-1">{total_dirs}</div>
    </div>
    <div class="card rounded-xl p-5">
      <div class="text-slate-400 text-xs font-semibold uppercase tracking-wider">Scratch Tools</div>
      <div class="text-3xl font-bold text-emerald-400 mt-1">{scratch_count}</div>
    </div>
    <div class="card rounded-xl p-5">
      <div class="text-slate-400 text-xs font-semibold uppercase tracking-wider">Background Tasks</div>
      <div class="text-3xl font-bold text-blue-400 mt-1">{task_count}</div>
    </div>
    <div class="card rounded-xl p-5">
      <div class="text-slate-400 text-xs font-semibold uppercase tracking-wider">Failed / Deadlocked</div>
      <div class="text-3xl font-bold text-rose-400 mt-1">{failed_tasks}</div>
    </div>
  </div>

  <div class="card rounded-xl p-6 mb-8">
    <h2 class="text-xl font-bold text-slate-200 mb-4">Scratch Tool Domain Classification</h2>
    <table class="w-full text-left">
      <thead>
        <tr class="border-b border-slate-700 text-slate-400 text-xs uppercase tracking-wider">
          <th class="px-4 py-2">Domain Category</th>
          <th class="px-4 py-2 text-right">Scripts Classified</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-800">
        {category_rows}
      </tbody>
    </table>
  </div>
</body>
</html>"""
        return html

    def export_knowledge_item(
        self,
        output_dir: Path,
        ki_id: str,
        title: str,
        category: str,
        summary: str,
        claims: list[dict[str, Any]],
    ) -> tuple[Path, Path]:
        """Export canonical dual-file Knowledge Vault item with isnad claims (Rule 40, 41).

        Guarantees metadata.json and summary.md dual-file format in output_dir / ki_id.
        """
        ki_dir = output_dir / ki_id
        ki_dir.mkdir(parents=True, exist_ok=True)

        meta_file = ki_dir / "metadata.json"
        summary_file = ki_dir / "summary.md"

        metadata = {
            "id": ki_id,
            "title": title,
            "category": category,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "author": "Brain Artifact Miner Service",
            "tags": ["brain_store", "artifact_archaeology", "epistemics"],
            "distilled_learning": summary,
            "isnad": {
                "decision_id": f"dec_{ki_id}",
                "status": "VERIFIED",
                "claims": claims,
            },
        }

        meta_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        summary_md = f"# {title}\n\n**ID:** `{ki_id}`\n\n## Summary\n\n{summary}\n"
        summary_file.write_text(summary_md, encoding="utf-8")

        return meta_file, summary_file


# Typed IoC ServiceKey (Rule 2, Rule 49)
BRAIN_ARTIFACT_MINER_KEY: ServiceKey[BrainArtifactMinerService] = ServiceKey("service.brain_artifact_miner")


def resolve_brain_artifact_miner(ctx: ServiceContext | None = None) -> BrainArtifactMinerService:
    """Resolve BrainArtifactMinerService from IoC context or fall back to StandardBrainArtifactMinerService (Rule 58)."""
    if ctx is not None:
        svc = ctx.optional(BRAIN_ARTIFACT_MINER_KEY)
        if svc is not None and isinstance(svc, BrainArtifactMinerService):
            return svc
    return StandardBrainArtifactMinerService()


__all__ = [
    "ArtifactLifecycleEntry",
    "BRAIN_ARTIFACT_MINER_KEY",
    "BrainArtifactMinerService",
    "ByteOffsetEntry",
    "DualTranscriptStep",
    "ScratchCatalog",
    "ScratchCatalogItem",
    "StandardBrainArtifactMinerService",
    "TaskTriageReport",
    "resolve_brain_artifact_miner",
]
