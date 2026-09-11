"""Skill Pipeline Engine — authoritative kernel service and base abstractions for skill drivers.

Provides:
    1. Slotted and frozen domain value objects (SkillStageResult, SkillPipelineReport) (Rule 12 & Rule 43)
    2. BaseSkillPipelineEngine: Standardized stage execution, timing, error trapping, and telemetry
    3. Windows UTF-8 stream entrypoint invariant (Rule 23)
    4. Typed ServiceKey for IoC container registration (Rule 2)
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import structlog

from harness.kernel.context import ServiceKey

logger = structlog.get_logger()

# Enforce Windows UTF-8 stream codec entrypoint invariant (Rule 23)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


@dataclass(slots=True, frozen=True)
class SkillStageResult:
    """Immutable execution record of a single skill pipeline stage (Rule 12 & Rule 43)."""

    stage_num: int
    stage_name: str
    passed: bool
    duration_ms: float
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        assert 1 <= self.stage_num <= 20, f"Stage number {self.stage_num} out of valid range [1, 20]"
        assert self.stage_name.strip(), "stage_name cannot be empty"
        assert self.duration_ms >= 0.0, f"duration_ms cannot be negative: {self.duration_ms}"


@dataclass(slots=True, frozen=True)
class SkillPipelineReport:
    """Immutable report aggregating complete skill pipeline execution (Rule 12 & Rule 43)."""

    skill_name: str
    passed: bool
    stages: tuple[SkillStageResult, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        assert self.skill_name.strip(), "skill_name cannot be empty"

    @property
    def total_stages(self) -> int:
        return len(self.stages)

    @property
    def passed_stages_count(self) -> int:
        return sum(1 for s in self.stages if s.passed)

    @property
    def failed_stages_count(self) -> int:
        return sum(1 for s in self.stages if not s.passed)

    @property
    def total_duration_ms(self) -> float:
        return sum(s.duration_ms for s in self.stages)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to JSON-serializable dictionary."""
        return {
            "skill_name": self.skill_name,
            "passed": self.passed,
            "total_stages": self.total_stages,
            "passed_stages": self.passed_stages_count,
            "failed_stages": self.failed_stages_count,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "stages": [
                {
                    "stage_num": s.stage_num,
                    "stage_name": s.stage_name,
                    "passed": s.passed,
                    "duration_ms": round(s.duration_ms, 2),
                    "message": s.message,
                    "details": s.details,
                }
                for s in self.stages
            ],
            "metadata": self.metadata,
        }


class BaseSkillPipelineEngine:
    """Authoritative base engine for executing skill workflow pipelines.

    Provides high-resolution execution timing, automatic error containment,
    telemetry event dispatch, and report synthesis.
    """

    def __init__(
        self,
        skill_name: str,
        workspace_root: Path | str = ".",
        event_bus: Any | None = None,
    ) -> None:
        self.skill_name = skill_name.strip().lower().replace("_", "-")
        self.workspace_root = Path(workspace_root).resolve()
        self.event_bus = event_bus

    def execute_stage(
        self,
        stage_num: int,
        stage_name: str,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> SkillStageResult:
        """Execute an individual stage function with high-resolution timing and defensive error trapping."""
        start_time = time.perf_counter()
        try:
            res = fn(*args, **kwargs)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # If fn returns a tuple of (passed, message, details) or SkillStageResult
            if isinstance(res, SkillStageResult):
                return res
            elif isinstance(res, tuple) and len(res) >= 2:
                passed = bool(res[0])
                msg = str(res[1])
                details = res[2] if len(res) > 2 and isinstance(res[2], dict) else {}
            elif isinstance(res, bool):
                passed = res
                msg = "Stage completed successfully" if passed else "Stage check failed"
                details = {}
            else:
                passed = True
                msg = str(res) if res is not None else "Stage completed"
                details = {}

            stage_result = SkillStageResult(
                stage_num=stage_num,
                stage_name=stage_name,
                passed=passed,
                duration_ms=duration_ms,
                message=msg,
                details=details,
            )

        except Exception as err:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning(
                "Skill stage raised exception",
                skill=self.skill_name,
                stage=stage_num,
                error=str(err),
            )
            stage_result = SkillStageResult(
                stage_num=stage_num,
                stage_name=stage_name,
                passed=False,
                duration_ms=duration_ms,
                message=f"Error: {type(err).__name__} - {err}",
                details={"error_type": type(err).__name__, "error_str": str(err)},
            )

        # Dispatch telemetry to event bus if present
        if self.event_bus is not None:
            try:
                self.event_bus.publish({
                    "type": "skill.stage.completed",
                    "skill_name": self.skill_name,
                    "stage_num": stage_result.stage_num,
                    "stage_name": stage_result.stage_name,
                    "passed": stage_result.passed,
                    "duration_ms": stage_result.duration_ms,
                })
            except Exception:
                pass

        return stage_result

    def compile_report(
        self,
        stages: list[SkillStageResult] | tuple[SkillStageResult, ...],
        metadata: dict[str, Any] | None = None,
    ) -> SkillPipelineReport:
        """Aggregate stage results into an immutable pipeline execution report."""
        stage_tuple = tuple(stages)
        all_passed = all(s.passed for s in stage_tuple) and len(stage_tuple) > 0

        return SkillPipelineReport(
            skill_name=self.skill_name,
            passed=all_passed,
            stages=stage_tuple,
            metadata=metadata or {},
        )


# --- Authoritative Skill Driver Resolver (Rule 12: Slotted & Frozen) ---

@dataclass(slots=True, frozen=True)
class SkillDriverResolver:
    """Authoritative resolver and execution engine for agent skill workflow drivers.

    Resolves execution entrypoints via:
    1. Explicit declarative entrypoint in config.default.yaml or .agents/skills.config.yaml (Rule 44)
    2. Weighted pattern heuristic ranking (pipeline > run_ > driver > main > engine)
    3. Alphabetical fallback
    """

    @classmethod
    def resolve_driver(cls, skill_dir: Path | str, workspace_root: Path | str | None = None) -> Path | None:
        """Resolve the executable driver Python script for a skill directory."""
        s_dir = Path(skill_dir).resolve()
        if not s_dir.exists():
            return None

        ws_root = Path(workspace_root).resolve() if workspace_root else s_dir.parent.parent.parent

        # 1. Check zero-fork configuration layers (Rule 44)
        # 1a. Project override: .agents/skills.config.yaml
        entrypoint_candidate: str | None = None
        proj_config = ws_root / ".agents" / "skills.config.yaml"
        if proj_config.exists():
            try:
                import yaml
                data = yaml.safe_load(proj_config.read_text(encoding="utf-8")) or {}
                skill_conf = data.get(s_dir.name) or {}
                if "entrypoint" in skill_conf:
                    entrypoint_candidate = str(skill_conf["entrypoint"]).strip()
            except Exception:
                pass

        # 1b. Skill default: config.default.yaml
        if not entrypoint_candidate:
            default_config = s_dir / "config.default.yaml"
            if default_config.exists():
                try:
                    import yaml
                    data = yaml.safe_load(default_config.read_text(encoding="utf-8")) or {}
                    if "entrypoint" in data:
                        entrypoint_candidate = str(data["entrypoint"]).strip()
                except Exception:
                    pass

        # If explicit entrypoint declared, attempt resolution
        if entrypoint_candidate:
            cand_path = s_dir / entrypoint_candidate
            if cand_path.is_file():
                return cand_path.resolve()
            cand_ws = ws_root / entrypoint_candidate
            if cand_ws.is_file():
                return cand_ws.resolve()

        # 2. Inspect scripts/ directory
        scripts_dir = s_dir / "scripts"
        candidates_dir = scripts_dir if scripts_dir.is_dir() else s_dir
        py_files = [f for f in sorted(candidates_dir.glob("*.py")) if not f.name.startswith("__")]

        if not py_files:
            return None

        # 3. Score candidates by architectural priority heuristic
        def _score_file(p: Path) -> int:
            lower = p.name.lower()
            if "pipeline" in lower:
                return 100
            if lower.startswith("run_") or "driver" in lower:
                return 80
            if lower == "main.py":
                return 60
            if lower.startswith("engine"):
                return 40
            return 10

        max_score = max(_score_file(f) for f in py_files)
        top_candidates = sorted([f for f in py_files if _score_file(f) == max_score], key=lambda f: f.name)
        return top_candidates[0].resolve()

    @classmethod
    def execute_driver(
        cls,
        skill_name: str,
        root_path: Path | str = ".",
        source: str | None = None,
        timeout_seconds: float = 300.0,
    ) -> dict[str, Any]:
        """Execute an automated skill driver with timeout protection and UTF-8 stream capture."""
        clean_name = skill_name.strip().lower().replace("_", "-")
        root = Path(root_path).resolve()
        skill_dir = root / ".agents" / "skills" / clean_name
        if not skill_dir.exists():
            skill_dir = root / "skills" / clean_name

        if not skill_dir.exists():
            return {"status": "error", "reason": f"Skill directory not found: {skill_dir}"}

        scripts_dir = skill_dir / "scripts"
        if not scripts_dir.exists() and not any(skill_dir.glob("*.py")):
            return {"status": "error", "reason": f"Skill does not contain a scripts/ directory: {scripts_dir}"}

        driver_path = cls.resolve_driver(skill_dir, workspace_root=root)
        if driver_path is None or not driver_path.is_file():
            return {"status": "error", "reason": f"No Python driver scripts found in {scripts_dir}"}

        import subprocess
        cmd = [sys.executable, str(driver_path)]
        if source:
            cmd.append(source)

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                encoding="utf-8",
                errors="replace",
            )
            return {
                "status": "ok" if proc.returncode == 0 else "error",
                "returncode": proc.returncode,
                "skill_name": clean_name,
                "driver": driver_path.name,
                "driver_path": str(driver_path),
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "status": "error",
                "returncode": -1,
                "skill_name": clean_name,
                "driver": driver_path.name,
                "driver_path": str(driver_path),
                "stdout": exc.stdout or "",
                "stderr": f"Subprocess timed out after {timeout_seconds}s (Rule 25)",
            }
        except Exception as exc:
            return {
                "status": "error",
                "returncode": -1,
                "skill_name": clean_name,
                "driver": driver_path.name,
                "driver_path": str(driver_path),
                "stdout": "",
                "stderr": str(exc),
            }


SKILL_PIPELINE_ENGINE_KEY: ServiceKey[BaseSkillPipelineEngine] = ServiceKey("service.skill_pipeline_engine")

__all__ = [
    "BaseSkillPipelineEngine",
    "SKILL_PIPELINE_ENGINE_KEY",
    "SkillDriverResolver",
    "SkillPipelineReport",
    "SkillStageResult",
]
