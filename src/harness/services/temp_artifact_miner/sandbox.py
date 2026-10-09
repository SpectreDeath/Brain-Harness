"""Pytest Sandbox Triage and Bounded Log Ring-Buffer (Rule 52, Rule 53)."""

from __future__ import annotations

import logging
from collections import deque
from pathlib import Path

from harness.services.temp_artifact_miner.models import (
    PRUNE_NAMES,
    SandboxFixture,
    SandboxReport,
)

logger = logging.getLogger("harness.services.temp_artifact_miner")


def triage_sandbox(
    pytest_dir: Path | str | None = None,
    max_depth: int = 3,
    default_temp_dir: Path | None = None,
) -> SandboxReport:
    """Triage ephemeral pytest sandbox directories (pytest-of-spectre/pytest-*).

    Enforces bounded traversal and noise pruning (Rule 52).
    """
    if pytest_dir is not None:
        target_path = Path(pytest_dir)
    elif default_temp_dir is not None:
        target_path = default_temp_dir
    else:
        target_path = Path(".")

    sandbox_root = target_path / "pytest-of-spectre"
    if not sandbox_root.exists():
        # Check for generic pytest-of-* directory if pytest-of-spectre not found
        candidates = list(target_path.glob("pytest-of-*"))
        if candidates:
            sandbox_root = candidates[0]
        else:
            return SandboxReport(total_runs=0, sandbox_path=str(sandbox_root), runs=(), error_snippets=())

    runs: list[SandboxFixture] = []
    try:
        run_dirs = sorted(
            [d for d in sandbox_root.iterdir() if d.is_dir() and d.name.startswith("pytest-")],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except Exception as e:
        logger.warning("Error listing pytest sandbox directories: %s", e)
        return SandboxReport(total_runs=0, sandbox_path=str(sandbox_root), runs=(), error_snippets=())

    for r_dir in run_dirs[:10]:
        fixtures: list[str] = []
        mock_skills: list[str] = []
        try:
            for sub in r_dir.iterdir():
                if sub.name in PRUNE_NAMES:
                    continue
                if sub.is_dir():
                    fixtures.append(sub.name)
                    skills_dir = sub / "skills"
                    if skills_dir.exists() and skills_dir.is_dir():
                        for s in skills_dir.iterdir():
                            if s.is_dir() and s.name not in PRUNE_NAMES:
                                mock_skills.append(s.name)
        except Exception as e:
            logger.warning("Error inspecting pytest run %s: %s", r_dir.name, e)

        runs.append(
            SandboxFixture(
                name=r_dir.name,
                path=str(r_dir),
                fixture_count=len(fixtures),
                mock_skills=tuple(mock_skills),
            )
        )

    return SandboxReport(
        total_runs=len(runs),
        sandbox_path=str(sandbox_root),
        runs=tuple(runs),
        error_snippets=(),
    )


def tail_diagnostic_log(
    log_path: Path | str,
    max_lines: int = 50,
) -> tuple[str, ...]:
    """Read the trailing lines of an ephemeral diagnostic log into a bounded ring buffer (Rule 53)."""
    target = Path(log_path)
    if not target.exists():
        return ()
    buffer: deque[str] = deque(maxlen=max_lines)
    try:
        with open(target, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                buffer.append(line.rstrip())
    except Exception as e:
        logger.warning("Error reading diagnostic log %s: %s", target.name, e)
    return tuple(buffer)
