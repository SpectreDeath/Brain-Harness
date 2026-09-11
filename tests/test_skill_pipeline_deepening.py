"""Contract test suite for deepened Skill Pipeline Engine and Registry seams."""

from __future__ import annotations

from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.commands.skills import list_skills_cmd, run_skill_cmd, skills_group
from harness.services.skill_graph import BuiltinSkillRegistryService
from harness.services.skill_pipeline import (
    BaseSkillPipelineEngine,
    SkillDriverResolver,
    SkillPipelineReport,
    SkillStageResult,
)


@pytest.mark.unit
class TestSkillPipelineEngineAndEntities:
    """Validate slotted/frozen dataclass immutability and BaseSkillPipelineEngine execution."""

    def test_slotted_frozen_dataclass_immutability(self) -> None:
        """Assert slotted and frozen dataclass invariants (Rule 12 & Rule 43)."""
        stage = SkillStageResult(
            stage_num=1,
            stage_name="Analyze",
            passed=True,
            duration_ms=12.5,
            message="OK",
        )
        with pytest.raises((AttributeError, TypeError)):
            stage.passed = False  # type: ignore

        report = SkillPipelineReport(
            skill_name="test-pipeline",
            passed=True,
            stages=(stage,),
        )
        with pytest.raises((AttributeError, TypeError)):
            report.passed = False  # type: ignore

    def test_stage_result_post_init_validation(self) -> None:
        """Assert validation rules on stage numbers and names."""
        with pytest.raises(AssertionError):
            SkillStageResult(
                stage_num=0,  # Invalid <= 0
                stage_name="Invalid",
                passed=True,
                duration_ms=1.0,
                message="Bad",
            )

        with pytest.raises(AssertionError):
            SkillStageResult(
                stage_num=1,
                stage_name="",  # Empty name
                passed=True,
                duration_ms=1.0,
                message="Bad",
            )

    def test_base_pipeline_engine_stage_execution(self) -> None:
        """Assert BaseSkillPipelineEngine runs stages with duration tracking and error trapping."""
        engine = BaseSkillPipelineEngine(skill_name="sample-engine")

        # 1. Successful stage
        def success_step(val: int) -> tuple[bool, str, dict[str, int]]:
            return True, f"Calculated {val * 2}", {"val": val * 2}

        res = engine.execute_stage(1, "Step Success", success_step, 10)
        assert res.passed is True
        assert res.stage_num == 1
        assert res.duration_ms >= 0.0
        assert "20" in res.message
        assert res.details == {"val": 20}

        # 2. Failing stage raising exception
        def failing_step() -> None:
            raise ValueError("Simulated failure in step")

        err_res = engine.execute_stage(2, "Step Failure", failing_step)
        assert err_res.passed is False
        assert "ValueError" in err_res.message
        assert err_res.details["error_type"] == "ValueError"

        # 3. Compile report
        report = engine.compile_report([res, err_res])
        assert report.passed is False
        assert report.total_stages == 2
        assert report.passed_stages_count == 1
        assert report.failed_stages_count == 1
        assert report.total_duration_ms > 0.0

        # 4. JSON serialization
        d = report.to_dict()
        assert d["skill_name"] == "sample-engine"
        assert d["passed"] is False
        assert len(d["stages"]) == 2


@pytest.mark.unit
class TestBuiltinSkillRegistryDelegation:
    """Validate BuiltinSkillRegistryService delegates parsing to SkillCardParser."""

    def test_registry_populates_invariants_and_triggers(self) -> None:
        """Assert that all skills discovered by BuiltinSkillRegistryService now have invariants populated."""
        registry = BuiltinSkillRegistryService(default_root=".")
        skills = registry.discover_all(".")
        assert len(skills) >= 42

        # Check legacy-modernization-pipeline
        mod_skill = registry.get_skill("legacy-modernization-pipeline")
        assert mod_skill is not None
        assert mod_skill.name == "legacy-modernization-pipeline"
        assert len(mod_skill.stages) >= 5
        assert len(mod_skill.anti_patterns) >= 5
        assert len(mod_skill.invariants) >= 5, "Invariants must be populated via SkillCardParser delegation"
        assert all(inv.is_blocking for inv in mod_skill.invariants)

        # Check triggers parsed from CARD.md
        assert any("characterization testing" in t for t in mod_skill.triggers)


@pytest.mark.unit
class TestSkillsCLISeams:
    """Validate headless CLI subcommands (skills list, skills run)."""

    def test_cli_skills_list(self) -> None:
        """Assert harness skills list returns table with all skills."""
        runner = CliRunner()
        res = runner.invoke(skills_group, ["list"])
        assert res.exit_code == 0
        assert "Registered Agent Skills" in res.output
        assert "legacy-modernization-pipeline" in res.output
        assert "multimedia-intelligence-forge" in res.output
        assert "rules" in res.output

    def test_cli_skills_list_with_category_filter(self) -> None:
        """Assert category filter works on skills list."""
        runner = CliRunner()
        res = runner.invoke(skills_group, ["list", "--category", "agent_orchestration / meta-skills"])
        assert res.exit_code == 0
        assert "swarm-reflection-optimizer" in res.output

    def test_cli_skills_run_and_programmatic_seam(self) -> None:
        """Assert run_skill_cmd executes driver headlessly (Rule 10)."""
        res = run_skill_cmd("legacy-modernization-pipeline")
        assert res["status"] == "ok"
        assert res["returncode"] == 0
        assert "modernization_orchestrator.py" in res["driver"]

        # Run via Click CLI
        runner = CliRunner()
        cli_res = runner.invoke(skills_group, ["run", "legacy-modernization-pipeline"])
        assert cli_res.exit_code == 0
        assert "Executing skill pipeline" in cli_res.output
        assert "COMPLETED" in cli_res.output


@pytest.mark.unit
class TestSkillDriverResolverDeepened:
    """Validate authoritative driver resolution, config-driven entrypoints, and heuristic scoring."""

    def test_resolve_driver_explicit_config_entrypoint(self, tmp_path: Path) -> None:
        """Assert explicit entrypoint in config.default.yaml overrides alphabetical script ordering (Rule 44)."""
        skill_dir = tmp_path / "custom-skill"
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(parents=True)

        # Create multiple scripts where alphabetical order would pick alpha.py
        (scripts_dir / "alpha_helper.py").write_text("# alpha", encoding="utf-8")
        (scripts_dir / "beta_util.py").write_text("# beta", encoding="utf-8")
        (scripts_dir / "special_runner.py").write_text("# runner", encoding="utf-8")

        # Declare explicit entrypoint
        (skill_dir / "config.default.yaml").write_text(
            "entrypoint: 'scripts/special_runner.py'\n",
            encoding="utf-8",
        )

        resolved = SkillDriverResolver.resolve_driver(skill_dir)
        assert resolved is not None
        assert resolved.name == "special_runner.py"

    def test_resolve_driver_heuristic_ranking(self, tmp_path: Path) -> None:
        """Assert heuristic pattern scoring picks *pipeline*.py or run_*.py over alphabetical utilities."""
        skill_dir = tmp_path / "multi-script-skill"
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(parents=True)

        # Alphabetical first would be a_linter.py
        (scripts_dir / "a_linter.py").write_text("# linter", encoding="utf-8")
        (scripts_dir / "engine.py").write_text("# engine", encoding="utf-8")
        (scripts_dir / "run_pipeline.py").write_text("# pipeline", encoding="utf-8")

        resolved = SkillDriverResolver.resolve_driver(skill_dir)
        assert resolved is not None
        assert resolved.name == "run_pipeline.py"

    def test_execute_driver_returns_backward_compatible_contract(self) -> None:
        """Assert execute_driver returns standard dict with status, returncode, driver, stdout, and stderr."""
        res = SkillDriverResolver.execute_driver("legacy-modernization-pipeline")
        assert res["status"] == "ok"
        assert res["returncode"] == 0
        assert "driver" in res
        assert "stdout" in res
        assert "stderr" in res
        assert "modernization_orchestrator.py" in res["driver"]

