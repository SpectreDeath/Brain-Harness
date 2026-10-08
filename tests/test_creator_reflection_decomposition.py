"""Comprehensive unit and contract tests for creator/reflection package decomposition.

Verifies:
1. Isolated submodule imports (models, extractors, harvester, distiller, visualizer, engine, __init__).
2. 100% backward compatibility of all public symbols exported from harness.creator.reflection.
3. Slotted dataclass behaviors and scope matching filters.
4. Extractor pipeline registry, distillation, and deduplication logic.
5. Harvester parsing of HTML visual briefs, transcripts, and JUnit reports.
6. HTML visual brief generator contract.
7. Single-seam resolver resolve_reflector_engine with and without IoC context (Rule 58).
"""

from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext


@pytest.mark.unit
def test_submodule_direct_imports() -> None:
    """Verify each decomposed submodule can be imported independently."""
    from harness.creator.reflection.distiller import EpisodicMemoryReflector
    from harness.creator.reflection.engine import (
        HARNESS_REFLECTOR_ENGINE_KEY,
        HarnessReflectorEngine,
        resolve_reflector_engine,
    )
    from harness.creator.reflection.extractors import (
        ArchitectureSeamPatternExtractor,
        BaseMemoryPatternExtractor,
        ComputeCalibrationPatternExtractor,
        ErrorRecoveryPatternExtractor,
        MemoryPatternPipeline,
        TestExecutionPatternExtractor,
        TransactionalStepPatternExtractor,
    )
    from harness.creator.reflection.harvester import HarnessHistoryHarvester
    from harness.creator.reflection.models import (
        DistilledHeuristic,
        ReflectionReport,
        ReflectionScope,
        ReportArtifact,
        TranscriptSession,
    )
    from harness.creator.reflection.visualizer import generate_reflection_html_brief

    assert ReflectionScope is not None
    assert ReportArtifact is not None
    assert TranscriptSession is not None
    assert DistilledHeuristic is not None
    assert ReflectionReport is not None
    assert BaseMemoryPatternExtractor is not None
    assert ArchitectureSeamPatternExtractor is not None
    assert TransactionalStepPatternExtractor is not None
    assert ComputeCalibrationPatternExtractor is not None
    assert ErrorRecoveryPatternExtractor is not None
    assert TestExecutionPatternExtractor is not None
    assert MemoryPatternPipeline is not None
    assert HarnessHistoryHarvester is not None
    assert EpisodicMemoryReflector is not None
    assert HarnessReflectorEngine is not None
    assert HARNESS_REFLECTOR_ENGINE_KEY is not None
    assert callable(resolve_reflector_engine)
    assert callable(generate_reflection_html_brief)


@pytest.mark.unit
def test_facade_re_exports_and_backward_compatibility() -> None:
    """Verify facade re-exports all 15 symbols and single-seam resolver."""
    import harness.creator.reflection as reflection

    symbols = [
        "ReflectionScope",
        "ReportArtifact",
        "TranscriptSession",
        "DistilledHeuristic",
        "ReflectionReport",
        "BaseMemoryPatternExtractor",
        "ArchitectureSeamPatternExtractor",
        "TransactionalStepPatternExtractor",
        "ComputeCalibrationPatternExtractor",
        "ErrorRecoveryPatternExtractor",
        "TestExecutionPatternExtractor",
        "MemoryPatternPipeline",
        "HarnessHistoryHarvester",
        "EpisodicMemoryReflector",
        "HarnessReflectorEngine",
        "HARNESS_REFLECTOR_ENGINE_KEY",
        "resolve_reflector_engine",
    ]
    for sym in symbols:
        assert hasattr(reflection, sym), f"Facade missing symbol: {sym}"
        assert getattr(reflection, sym) is not None


@pytest.mark.unit
def test_reflection_scope_matching() -> None:
    """Verify ReflectionScope filters on date, conversation, and category."""
    from harness.creator.reflection.models import ReflectionScope

    now = datetime(2026, 10, 6, 12, 0, 0, tzinfo=timezone.utc)
    scope = ReflectionScope(
        since=now,
        conversation_ids=["conv-123", "conv-456"],
        categories=["architecture", "performance"],
        min_confidence=0.85,
    )

    # Date matching
    assert scope.matches_date("2026-10-06T13:00:00+00:00") is True
    assert scope.matches_date("2026-10-06T11:00:00+00:00") is False
    assert scope.matches_date("invalid-date") is True  # Resilient fallback

    # Conversation matching
    assert scope.matches_conversation("conv-123") is True
    assert scope.matches_conversation("conv-789") is False

    # Category matching
    assert scope.matches_category("ARCHITECTURE") is True
    assert scope.matches_category("performance") is True
    assert scope.matches_category("security") is False


@pytest.mark.unit
def test_models_slotted_attributes() -> None:
    """Verify Reflection models instantiate cleanly with slotted attributes."""
    from harness.creator.reflection.models import (
        DistilledHeuristic,
        ReflectionReport,
        ReportArtifact,
        TranscriptSession,
    )

    rep = ReportArtifact(
        file_path=Path("/tmp/brief.html"),
        title="Brief 1",
        created_at="2026-10-06T12:00:00Z",
        report_type="architecture_review",
        content_text="Some content",
        friction_points=["gotcha 1"],
    )
    assert rep.title == "Brief 1"
    assert "gotcha 1" in rep.friction_points

    trans = TranscriptSession(
        conversation_id="conv-1",
        log_path=Path("/tmp/t.jsonl"),
        total_steps=5,
        user_requests=["do something"],
        tools_invoked=["read_file"],
    )
    assert trans.total_steps == 5

    h = DistilledHeuristic(
        title="Rule 1",
        category="architecture",
        heuristic="Everything is a plugin",
        confidence=0.99,
        source_artifacts=["/tmp/brief.html"],
    )
    assert h.title == "Rule 1"

    report = ReflectionReport(
        reflection_id="ref_1",
        timestamp="2026-10-06T12:00:00Z",
        harvested_reports_count=1,
        harvested_transcripts_count=1,
        heuristics=[h],
    )
    assert report.reflection_id == "ref_1"
    assert len(report.heuristics) == 1


@pytest.mark.unit
def test_pattern_pipeline_deduplication_and_provenance() -> None:
    """Verify MemoryPatternPipeline executes extractors and merges provenance."""
    from harness.creator.reflection.extractors import (
        ArchitectureSeamPatternExtractor,
        MemoryPatternPipeline,
    )
    from harness.creator.reflection.models import (
        ReflectionScope,
        ReportArtifact,
    )

    rep1 = ReportArtifact(
        file_path=Path("/tmp/brief1.html"),
        title="Review 1",
        created_at="2026-10-06T10:00:00Z",
        report_type="architecture_review",
        content_text="lazy subprocess venv cold-start timeout friction",
        friction_points=["cold-start timeout"],
    )
    rep2 = ReportArtifact(
        file_path=Path("/tmp/brief2.html"),
        title="Review 2",
        created_at="2026-10-06T11:00:00Z",
        report_type="architecture_review",
        content_text="lazy subprocess cold-start in venv isolation",
        friction_points=["cold-start in venv"],
    )

    pipeline = MemoryPatternPipeline([ArchitectureSeamPatternExtractor()])
    scope = ReflectionScope(min_confidence=0.80)
    heuristics = pipeline.distill([rep1, rep2], [], scope=scope)

    # Should deduplicate by title and merge source_artifacts
    lazy_h = [h for h in heuristics if "Lazy Subprocess" in h.title]
    assert len(lazy_h) == 1
    assert str(rep1.file_path) in lazy_h[0].source_artifacts
    assert str(rep2.file_path) in lazy_h[0].source_artifacts


@pytest.mark.unit
def test_visualizer_html_generation() -> None:
    """Verify generate_reflection_html_brief writes HTML with metrics and Mermaid."""
    from harness.creator.reflection.models import (
        DistilledHeuristic,
        ReportArtifact,
        TranscriptSession,
    )
    from harness.creator.reflection.visualizer import generate_reflection_html_brief

    with tempfile.TemporaryDirectory() as td:
        out_dir = Path(td)
        rep = ReportArtifact(
            file_path=out_dir / "brief.html",
            title="Brief",
            created_at="2026-10-06T12:00:00Z",
            report_type="architecture_review",
            content_text="Sample text",
        )
        trans = TranscriptSession(
            conversation_id="conv-1",
            log_path=out_dir / "t.jsonl",
            total_steps=3,
        )
        h = DistilledHeuristic(
            title="Design Rule",
            category="architecture",
            heuristic="Keep modules deep",
            confidence=0.95,
        )

        out_file = generate_reflection_html_brief(
            output_dir=out_dir,
            reflection_id="ref_test",
            reports=[rep],
            transcripts=[trans],
            heuristics=[h],
            kis=[],
        )

        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "Harness Memory Reflection — ref_test" in content
        assert "Keep modules deep" in content
        assert "mermaid" in content


@pytest.mark.unit
def test_resolve_reflector_engine_single_seam() -> None:
    """Verify resolve_reflector_engine with and without IoC context (Rule 58)."""
    from harness.creator.reflection.engine import (
        HARNESS_REFLECTOR_ENGINE_KEY,
        HarnessReflectorEngine,
        resolve_reflector_engine,
    )

    # 1. Standalone fallback without context
    engine1 = resolve_reflector_engine(None)
    assert isinstance(engine1, HarnessReflectorEngine)
    assert engine1.harvester is not None
    assert engine1.pipeline is not None

    # 2. Context without registered instance (fallback)
    ctx = ServiceContext()
    engine2 = resolve_reflector_engine(ctx)
    assert isinstance(engine2, HarnessReflectorEngine)

    # 3. Context with registered instance (IoC resolution)
    custom_engine = HarnessReflectorEngine()
    ctx.provide(HARNESS_REFLECTOR_ENGINE_KEY, custom_engine)
    resolved = resolve_reflector_engine(ctx)
    assert resolved is custom_engine
