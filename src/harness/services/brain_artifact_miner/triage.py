"""Background subprocess task log triage and stderr drainage (Rule 53)."""

from __future__ import annotations

import logging
import os
import re
import sys
from collections import deque
from pathlib import Path
from typing import Any

from harness.services.brain_artifact_miner.models import TaskTriageReport

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = logging.getLogger("harness.services.brain_artifact_miner.triage")


def triage_task_logs(brain_dir: Path, max_depth: int = 4) -> TaskTriageReport:
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


__all__ = ["triage_task_logs"]
