"""Tests for enterprise agent-skills-architect skill and Knowledge Vault items."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import pytest

from harness.creator.skills import SkillValidator


@pytest.mark.unit
def test_agent_skills_architect_validation() -> None:
    """Validate agent-skills-architect conforms to deep-module craft standards."""
    skill_dir = Path(".agents/skills/agent-skills-architect").resolve()
    assert skill_dir.is_dir(), f"Skill directory missing: {skill_dir}"
    
    report = SkillValidator.validate_sync(skill_dir)
    assert report.valid is True
    assert len(report.errors) == 0
    assert len(report.warnings) == 0


@pytest.mark.unit
def test_eval_uplift_calculator_logic() -> None:
    """Assert Google 2x2 uplift calculation logic and quadrant assignment."""
    import importlib.util

    script_path = Path(".agents/skills/agent-skills-architect/scripts/eval_uplift_calculator.py").resolve()
    assert script_path.exists()

    spec = importlib.util.spec_from_file_location("eval_uplift_calc", str(script_path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["eval_uplift_calc"] = module
    spec.loader.exec_module(module)

    # 1. Dominant Uplift Test Case
    baseline = module.RunMetric(
        run_id="base", accuracy_score=0.60, tokens_consumed=10000, latency_seconds=10.0, turns_count=4
    )
    with_skill = module.RunMetric(
        run_id="skill", accuracy_score=0.90, tokens_consumed=4000, latency_seconds=4.0, turns_count=2
    )
    result = module.calculate_uplift(baseline, with_skill)
    assert result.passed_gate is True
    assert result.quadrant == module.EvalQuadrant.DOMINANT_UPLIFT
    assert pytest.approx(result.accuracy_uplift, 0.01) == 0.30
    assert pytest.approx(result.token_efficiency_uplift_pct, 0.1) == 60.0

    # 2. Degraded Test Case
    degraded_skill = module.RunMetric(
        run_id="degraded", accuracy_score=0.50, tokens_consumed=15000, latency_seconds=15.0, turns_count=6
    )
    result_degraded = module.calculate_uplift(baseline, degraded_skill)
    assert result_degraded.passed_gate is False
    assert result_degraded.quadrant == module.EvalQuadrant.DEGRADED


@pytest.mark.unit
def test_knowledge_vault_items_conformity() -> None:
    """Verify all 3 Knowledge Vault items adhere to dual-file directory format."""
    base_dir = Path(".harness/knowledge")
    target_kis = [
        "ki_agent_skills_progressive_disclosure",
        "ki_google_agent_skills_enterprise_evals",
        "ki_agent_skills_runtime_security_middleware",
    ]

    for ki_id in target_kis:
        ki_dir = base_dir / ki_id
        assert ki_dir.is_dir(), f"Missing KI dir: {ki_dir}"
        meta_file = ki_dir / "metadata.json"
        summary_file = ki_dir / "summary.md"
        assert meta_file.is_file(), f"Missing metadata.json in {ki_dir}"
        assert summary_file.is_file(), f"Missing summary.md in {ki_dir}"

        with open(meta_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["id"] == ki_id
        assert "provenance" in data
        assert len(data["provenance"]) > 0

        summary_text = summary_file.read_text(encoding="utf-8")
        assert len(summary_text) > 100
        assert ki_id in summary_text
