"""Comprehensive characterization test suite for Media Mind Forge engine decomposition.

Validates:
1. Slotted and frozen dataclass architecture (Rules 12 and 43).
2. Domain-partitioned submodules:
   - models: Slotted data structures for transcripts, isnad claims, thematic points.
   - transcripts: Multi-format transcript normalization, timeline segmentation, WPM.
   - distillation: Mind-Reader epistemic lens (mental models, heuristics, isnad grounding).
   - procedures: Forge procedural lens (Shu-Ha-Ri stages, diagnostic rubrics, anti-patterns).
   - brief: Interactive HTML visual brief report generation in %TEMP% with Mermaid DAG.
   - scaffolder: SKILL.md (Rule 37) and CARD.md (Rule 37 single-pipe borders) authoring.
   - core: Lean MediaMindForgeEngine coordinator delegating across submodules.
3. 100% backward compatibility for all external callers and entrypoints.
4. Plugin module singleton export (Rule 45).
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from plugins.memory_and_epistemics.media_mind_forge.engine import MediaMindForgeEngine
from plugins.memory_and_epistemics.media_mind_forge.engine.models import (
    DeconstructedTranscriptResult,
    IsnadClaimNode,
    SkillPackageResult,
    ThematicPoints,
)
from plugins.memory_and_epistemics.media_mind_forge.engine.transcripts import (
    deconstruct_transcript,
    extract_thematic_points,
)
from plugins.memory_and_epistemics.media_mind_forge.engine.distillation import (
    distill_epistemic_models,
    distill_knowledge_items,
)
from plugins.memory_and_epistemics.media_mind_forge.engine.procedures import (
    synthesize_procedural_stages,
    synthesize_diagnostic_rubric,
    synthesize_anti_patterns,
)
from plugins.memory_and_epistemics.media_mind_forge.engine.brief import (
    generate_visual_brief_html,
)
from plugins.memory_and_epistemics.media_mind_forge.engine.scaffolder import (
    generate_skill_md_content,
    generate_card_md_content,
    scaffold_skill_directory,
)
from plugins.memory_and_epistemics.media_mind_forge.main import (
    MEDIA_MIND_FORGE_KEY,
    MediaMindForgePlugin,
    plugin,
)
from plugins.memory_and_epistemics.media_mind_forge.models import (
    CognitiveAnalysisReport,
    MentalModel,
    DecisionHeuristic,
    DiagnosticQuestion,
    ProceduralStage,
    AntiPatternItem,
    DistilledKnowledgeItem,
)


SAMPLE_TRANSCRIPT_TEXT = (
    "In this masterclass on ontological engineering, we explore Gruber's criteria for ontology design. "
    "First, clarity: definitions must be objective and formal. Second, coherence: inferences must be logically "
    "consistent. Third, extendibility: monotonic growth without breaking foundations. Fourth, minimal encoding bias. "
    "And fifth, minimal ontological commitment: asserting only what is strictly necessary. "
    "Guarino emphasizes the tension between precision and coverage. Formulate competency questions to bound the scope."
)

SAMPLE_TIMED_SEGMENTS = [
    {"text": "Welcome to the lecture on ontological engineering.", "start": 0.0, "duration": 4.5},
    {"text": "Gruber defined five criteria: clarity, coherence, extendibility, minimal encoding bias, and minimal commitment.", "start": 4.5, "duration": 8.0},
    {"text": "Guarino highlighted the precision vs coverage trade-off.", "start": 12.5, "duration": 5.5},
    {"text": "Always formulate competency questions to verify domain requirements.", "start": 18.0, "duration": 6.0},
]


@pytest.mark.unit
class TestMediaMindForgeSlottedModels:
    """Verify slotted and frozen dataclass architecture per Rules 12 and 43."""

    def test_deconstructed_transcript_result_immutability(self) -> None:
        result = DeconstructedTranscriptResult(
            clean_text="Clean transcript text",
            normalized_text="Clean transcript text",
            segments=(("Clean transcript text", 0.0, 5.0),),
            word_count=3,
            duration_s=5.0,
            duration_seconds=5.0,
            words_per_minute=36.0,
        )
        assert result.word_count == 3
        assert hasattr(result, "__slots__")

        # Rule 43: Direct attribute assignment inside pytest.raises((AttributeError, TypeError))
        with pytest.raises((AttributeError, TypeError)):
            result.word_count = 10  # type: ignore[misc]

    def test_isnad_claim_node_immutability(self) -> None:
        node = IsnadClaimNode(
            claim="Clarity requires formal objective definitions",
            speaker="Prof. Dr. Harald Sack",
            source="https://youtube.com/watch?v=abc12345678",
            timestamp_s=4.5,
            status="VERIFIED",
        )
        assert node.claim.startswith("Clarity")
        assert hasattr(node, "__slots__")

        with pytest.raises((AttributeError, TypeError)):
            node.status = "UNVERIFIED"  # type: ignore[misc]

    def test_skill_package_result_immutability(self) -> None:
        pkg = SkillPackageResult(
            skill_name="test-skill",
            skill_dir="/tmp/skills/test-skill",
            skill_file="/tmp/skills/test-skill/SKILL.md",
            card_file="/tmp/skills/test-skill/CARD.md",
        )
        assert pkg.skill_name == "test-skill"
        assert hasattr(pkg, "__slots__")

        with pytest.raises((AttributeError, TypeError)):
            pkg.skill_name = "mutated"  # type: ignore[misc]


@pytest.mark.unit
class TestDecomposedSubmodules:
    """Verify each decomposed domain submodule in isolation."""

    def test_transcripts_deconstruction_and_wpm(self) -> None:
        deconstructed = deconstruct_transcript(raw_text=SAMPLE_TRANSCRIPT_TEXT)
        assert deconstructed["word_count"] > 20
        assert deconstructed["duration_s"] > 0
        assert deconstructed["words_per_minute"] > 0
        assert len(deconstructed["segments"]) > 0

    def test_thematic_points_extraction(self) -> None:
        thematics = extract_thematic_points(SAMPLE_TRANSCRIPT_TEXT)
        assert len(thematics["first_principles"]) > 0
        assert any("Gruber" in fp for fp in thematics["first_principles"])
        assert len(thematics["heuristics"]) > 0
        assert any("Guarino" in h for h in thematics["heuristics"])

    def test_distillation_epistemic_models(self) -> None:
        mental_models, decision_heuristics = distill_epistemic_models(
            text=SAMPLE_TRANSCRIPT_TEXT,
            video_id="test1234567",
            speaker="Prof. Harald Sack",
        )
        assert len(mental_models) >= 3
        assert len(decision_heuristics) >= 2
        assert all(isinstance(m, MentalModel) for m in mental_models)
        assert all(isinstance(h, DecisionHeuristic) for h in decision_heuristics)

    def test_distillation_knowledge_items(self) -> None:
        kis = distill_knowledge_items(
            video_id="test1234567",
            speaker="Prof. Harald Sack",
            source_url="https://youtube.com/watch?v=test1234567",
        )
        assert len(kis) >= 2
        assert all(isinstance(ki, DistilledKnowledgeItem) for ki in kis)
        assert all(len(ki.isnad_claims) > 0 for ki in kis)

    def test_procedures_synthesis(self) -> None:
        stages = synthesize_procedural_stages()
        rubric = synthesize_diagnostic_rubric()
        anti_patterns = synthesize_anti_patterns()

        assert len(stages) >= 5
        assert len(rubric) >= 3
        assert len(anti_patterns) >= 3
        assert all(isinstance(s, ProceduralStage) for s in stages)
        assert all(isinstance(r, DiagnosticQuestion) for r in rubric)
        assert all(isinstance(ap, AntiPatternItem) for ap in anti_patterns)

    def test_visual_brief_generation(self) -> None:
        engine = MediaMindForgeEngine()
        report = engine.analyze(
            transcript_data=SAMPLE_TRANSCRIPT_TEXT,
            title="Ontological Engineering Test",
            speaker="Prof. Harald Sack",
            video_id="test1234567",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            brief_path = generate_visual_brief_html(report, target_dir=tmpdir)
            assert Path(brief_path).exists()
            content = Path(brief_path).read_text(encoding="utf-8")
            assert "<!DOCTYPE html>" in content
            assert "mermaid" in content
            assert "Ontological Engineering" in content

    def test_scaffolder_skill_and_card(self) -> None:
        engine = MediaMindForgeEngine()
        report = engine.analyze(transcript_data=SAMPLE_TRANSCRIPT_TEXT)

        # Rule 37 verification on generated SKILL.md
        skill_md = generate_skill_md_content(report, "test-ontology-coach")
        assert "## Anti-Patterns" in skill_md
        assert "- **" in skill_md
        assert " — " in skill_md

        # Rule 37 verification on generated CARD.md
        card_md = generate_card_md_content(report, "test-ontology-coach")
        assert "│" in card_md
        assert "║" not in card_md
        assert "## Mandatory Invariants Checklist" in card_md

        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = scaffold_skill_directory(report, output_dir=tmpdir, skill_name="test-ontology-coach")
            assert Path(pkg["skill_dir"]).exists()
            assert Path(pkg["skill_file"]).exists()
            assert Path(pkg["card_file"]).exists()


@pytest.mark.unit
class TestCoreEngineCoordinatorAndRule45:
    """Verify coordinator engine and Rule 45 module-level singleton export."""

    def test_coordinator_engine_facade_methods(self) -> None:
        engine = MediaMindForgeEngine()
        report = engine.analyze(
            transcript_data=SAMPLE_TIMED_SEGMENTS,
            title="Ontological Engineering Masterclass",
            speaker="Prof. Dr. Harald Sack",
            video_id="test1234567",
        )
        assert isinstance(report, CognitiveAnalysisReport)
        assert report.status == "ok"
        assert report.word_count > 0
        assert len(report.mental_models) >= 3
        assert len(report.decision_heuristics) >= 2
        assert len(report.procedural_stages) >= 5
        assert len(report.anti_patterns) >= 3
        assert len(report.knowledge_items) >= 2

    def test_plugin_module_singleton_rule_45(self) -> None:
        assert isinstance(plugin, MediaMindForgePlugin)
        assert MEDIA_MIND_FORGE_KEY in plugin.provides
        assert plugin.name == "media_mind_forge"
