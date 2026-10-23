"""Contract verification test suite for system-design-architect skill.

Verifies slotted and frozen dataclass architecture (Rule 12, Rule 43),
capacity calculation mathematics, 5-dimension interview evaluation logic,
canonical production case studies, and skill package hygiene.
"""

from __future__ import annotations

from pathlib import Path
import sys
import pytest

from harness.creator.skills import SkillValidator
from harness.services.skill_parser import SkillCardParser

SCRIPTS_DIR = Path(__file__).parent.parent / ".agents" / "skills" / "system-design-architect" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from system_design_engine import (
    CapacityEstimate,
    CaseStudy,
    DimensionScore,
    EvaluationReport,
    SystemDesignEngine,
)


@pytest.fixture
def skill_dir() -> Path:
    """Fixture providing path to system-design-architect skill directory."""
    path = Path(__file__).parent.parent / ".agents" / "skills" / "system-design-architect"
    if not path.exists():
        path = Path(".agents/skills/system-design-architect")
    return path


class TestSystemDesignDomainModels:
    """Verify Rule 12 and Rule 43 slotted and frozen dataclass invariants."""

    def test_capacity_estimate_immutability(self) -> None:
        """Verify CapacityEstimate is slotted and immutable (Rule 43)."""
        est = SystemDesignEngine.calculate_capacity(
            dau=1_000_000,
            read_write_ratio=10.0,
            reads_per_user_day=20.0,
        )
        assert est.dau == 1_000_000
        assert hasattr(est, "__slots__")

        with pytest.raises((AttributeError, TypeError)):
            est.dau = 2_000_000  # type: ignore[misc]

    def test_dimension_score_immutability_and_validation(self) -> None:
        """Verify DimensionScore asserts valid bounds and immutability."""
        ds = DimensionScore("Communication", 4, 0.20)
        assert ds.score == 4
        assert abs(ds.weighted_points - 16.0) < 1e-4  # (4/5) * 0.20 * 100

        with pytest.raises((AttributeError, TypeError)):
            ds.score = 5  # type: ignore[misc]

        with pytest.raises(ValueError):
            DimensionScore("Invalid Score", 6, 0.20)

        with pytest.raises(ValueError):
            DimensionScore("Negative Weight", 3, -0.10)

    def test_capacity_estimate_validation_assertions(self) -> None:
        """Verify CapacityEstimate rejects invalid construction values."""
        with pytest.raises(ValueError):
            SystemDesignEngine.calculate_capacity(dau=-100)

        with pytest.raises(ValueError):
            SystemDesignEngine.calculate_capacity(dau=1000, read_write_ratio=-5.0)

        with pytest.raises(ValueError):
            SystemDesignEngine.calculate_capacity(dau=1000, peak_multiplier=0.5)


class TestSystemDesignEngineCalculations:
    """Verify quantitative estimation and evaluation scoring mechanics."""

    def test_capacity_calculation_math(self) -> None:
        """Verify QPS, storage, and network bandwidth calculus."""
        est = SystemDesignEngine.calculate_capacity(
            dau=10_000_000,
            read_write_ratio=10.0,
            reads_per_user_day=50.0,
            avg_read_payload_bytes=4096,
            avg_write_payload_bytes=1024,
            peak_multiplier=3.0,
        )

        # 10M DAU * 50 reads = 500M daily reads / 86400 = 5787.037 read QPS
        assert abs(est.avg_read_qps - 5787.04) < 1.0
        assert abs(est.peak_read_qps - (est.avg_read_qps * 3.0)) < 0.01

        # Writes: 500M / 10 = 50M daily writes / 86400 = 578.70 write QPS
        assert abs(est.avg_write_qps - 578.70) < 1.0
        assert abs(est.peak_write_qps - (est.avg_write_qps * 3.0)) < 0.01

        # 5-Year storage must equal 5 * yearly storage
        assert est.five_year_storage_bytes == 5 * est.yearly_storage_bytes

        # Serialization to dictionary
        d = est.to_dict()
        assert d["dau"] == 10_000_000
        assert "daily_storage_gb" in d
        assert "five_year_storage_tb" in d

    def test_interview_evaluation_scorecard_thresholds(self) -> None:
        """Verify 5-dimension scorecard weights and recommendation bands."""
        # Strong Hire: All 5s -> 100%
        rep_strong = SystemDesignEngine.evaluate_interview(5, 5, 5, 5, 5)
        assert abs(rep_strong.weighted_percentage - 100.0) < 1e-4
        assert "Strong Hire" in rep_strong.hire_recommendation
        assert len(rep_strong.strengths) == 5

        # Hire: 4s across board -> 80%
        rep_hire = SystemDesignEngine.evaluate_interview(4, 4, 4, 4, 4)
        assert abs(rep_hire.weighted_percentage - 80.0) < 1e-4
        assert "Hire" in rep_hire.hire_recommendation

        # Leaning Hire: 3s across board -> 60%
        rep_leaning = SystemDesignEngine.evaluate_interview(3, 3, 3, 3, 3)
        assert abs(rep_leaning.weighted_percentage - 60.0) < 1e-4
        assert "Leaning Hire" in rep_leaning.hire_recommendation

        # No Hire: 2s across board -> 40%
        rep_no_hire = SystemDesignEngine.evaluate_interview(2, 2, 2, 2, 2)
        assert abs(rep_no_hire.weighted_percentage - 40.0) < 1e-4
        assert "No Hire" in rep_no_hire.hire_recommendation
        assert len(rep_no_hire.growth_areas) == 5

    def test_canonical_case_studies_retrieval(self) -> None:
        """Verify all three canonical case studies are retrievable with correct attributes."""
        spotify = SystemDesignEngine.get_canonical_case_study("spotify")
        assert "Spotify" in spotify.name
        assert "CDN" in spotify.primary_architecture

        booking = SystemDesignEngine.get_canonical_case_study("booking.com")
        assert "Booking.com" in booking.name
        assert "Redlock" in booking.concurrency_strategy or "lock" in booking.concurrency_strategy.lower()

        whatsapp = SystemDesignEngine.get_canonical_case_study("whatsapp")
        assert "WhatsApp" in whatsapp.name
        assert "WebSocket" in whatsapp.primary_architecture

        with pytest.raises(KeyError):
            SystemDesignEngine.get_canonical_case_study("nonexistent_system")


class TestSystemDesignSkillHygiene:
    """Verify package structural hygiene against SkillValidator and SkillCardParser."""

    @pytest.mark.asyncio
    async def test_skill_validator_passes(self, skill_dir: Path) -> None:
        """Assert that SkillValidator passes with zero critical or error diagnostics."""
        assert skill_dir.exists(), f"Skill directory missing: {skill_dir}"
        report = await SkillValidator.validate_async(skill_dir)
        assert report.valid is True, f"Skill validation failed: {report.errors}"

    def test_skill_card_parser_complete(self, skill_dir: Path) -> None:
        """Assert that SkillCardParser parses all stages, anti-patterns, and invariants."""
        parsed = SkillCardParser.parse_directory(skill_dir)
        assert parsed is not None
        assert parsed.name == "system-design-architect"

        # Verify stages (5 stages)
        assert len(parsed.stages) >= 5, f"Expected >= 5 stages, found {len(parsed.stages)}"
        stage_names = [s.name for s in parsed.stages]
        assert any("Requirements" in name for name in stage_names)
        assert any("Data & API" in name or "Data" in name for name in stage_names)
        assert any("High-Level" in name or "Architecture" in name for name in stage_names)
        assert any("Scale" in name or "Reliability" in name for name in stage_names)
        assert any("Trade-off" in name or "Extension" in name for name in stage_names)

        # Verify anti-patterns (>= 4)
        assert len(parsed.anti_patterns) >= 4, f"Expected >= 4 anti-patterns, found {len(parsed.anti_patterns)}"

        # Verify invariants (>= 4)
        assert len(parsed.invariants) >= 4, f"Expected >= 4 invariants, found {len(parsed.invariants)}"
        assert all(inv.is_blocking for inv in parsed.invariants)
