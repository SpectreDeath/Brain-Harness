"""Comprehensive unit and integration tests for media_mind_forge plugin.

Validates:
1. Transcript deconstruction, normalization, and pace metrics.
2. Dual-lens cognitive mining (epistemic mental models, heuristics, isnad grounding).
3. Procedural skill synthesis (Shu-Ha-Ri stages, diagnostic scorecards, anti-patterns).
4. Visual Brief HTML rendering in %TEMP% with embedded Mermaid DAG.
5. ServiceKey and IoC container registration via MediaMindForgePlugin.
6. SkillCardParser, SkillValidator, and PluginValidator schema compliance (Rules 34, 37, 38).
7. Skill Knowledge Graph router intent matching (Rule 35).
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import pytest

from harness.creator.skills import SkillValidator
from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.media_mind_forge.engine import MediaMindForgeEngine
from plugins.memory_and_epistemics.media_mind_forge.main import (
    MEDIA_MIND_FORGE_KEY,
    MediaMindForgePlugin,
    MediaMindForgeService,
    health,
    media_mind_forge_analyze,
    media_mind_forge_craft_skill,
    media_mind_forge_distill_kis,
    media_mind_forge_visual_brief,
)
from plugins.memory_and_epistemics.media_mind_forge.models import (
    AntiPatternItem,
    CognitiveAnalysisReport,
    DecisionHeuristic,
    DiagnosticQuestion,
    DistilledKnowledgeItem,
    MentalModel,
    ProceduralStage,
)
from plugins.memory_and_epistemics.skill_knowledge_graph.main import (
    index_skill_catalog,
    query_skill_router,
)
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser


SAMPLE_RAW_TRANSCRIPT = """
Welcome to this masterclass on Ontological Engineering and Knowledge Representation.
Today we explore first principles. First, what is an ontology?
In computer science, following Tom Gruber, an ontology is an explicit, formal specification of a shared conceptualization.
Nicola Guarino deepened this: an ontology is not just a vocabulary; it is an axiomatic theory restricting the possible models of a domain.
If two agents disagree on whether an entity is a state or an event, your distributed reasoning will collapse.
Here is the core heuristic: When modeling domain concepts, if a concept's identity criterion changes over time, model it as an Event, never an Entity.
Let us examine the stages of ontological engineering.
Stage one is Domain Scoping: Determine the exact boundary of what questions your ontology must answer.
Stage two is Conceptual Taxonomy: Establish clean subsumption (is-a) hierarchies without property conflation.
Stage three is Axiomatic Formalization: Write first-order logic or OWL axioms that prohibit nonsensical models.
A frequent anti-pattern is Property Hijacking: Reusing an existing class attribute with a completely different semantic meaning.
Another anti-pattern is Taxonomic Bleed: Subsuming physical objects under subjective operational roles.
Always verify your ontology with competency questions before deployment.
"""

SAMPLE_TIMED_SEGMENTS = [
    {"text": "Welcome to this masterclass on Ontological Engineering.", "start": 0.0, "duration": 4.5},
    {"text": "Following Tom Gruber, an ontology is an explicit specification of a conceptualization.", "start": 4.5, "duration": 6.0},
    {"text": "Guarino deepened this: an ontology is an axiomatic theory restricting possible models.", "start": 10.5, "duration": 7.0},
    {"text": "If a concept's identity changes over time, model it as an Event, never an Entity.", "start": 17.5, "duration": 5.5},
    {"text": "Stage one is Domain Scoping to determine exact competency boundaries.", "start": 23.0, "duration": 6.0},
    {"text": "Stage two is Conceptual Taxonomy establishing clean subsumption hierarchies.", "start": 29.0, "duration": 6.5},
    {"text": "A severe anti-pattern is Property Hijacking: reusing attributes with different semantics.", "start": 35.5, "duration": 8.0},
]


@pytest.mark.unit
class TestTranscriptDeconstruction:
    """Test text parsing, timing metrics, and segment normalization."""

    def test_deconstruct_raw_text(self) -> None:
        engine = MediaMindForgeEngine()
        metrics = engine.deconstruct_transcript(SAMPLE_RAW_TRANSCRIPT)

        assert metrics["word_count"] > 100
        assert metrics["duration_seconds"] > 0
        assert metrics["words_per_minute"] > 0
        assert len(metrics["segments"]) > 0
        assert "explicit, formal specification" in metrics["normalized_text"]

    def test_deconstruct_timed_segments(self) -> None:
        engine = MediaMindForgeEngine()
        metrics = engine.deconstruct_transcript(SAMPLE_TIMED_SEGMENTS)

        assert metrics["word_count"] > 40
        assert metrics["duration_seconds"] >= 43.5  # 35.5 + 8.0
        assert len(metrics["segments"]) == len(SAMPLE_TIMED_SEGMENTS)
        assert metrics["segments"][0]["start"] == 0.0
        assert "Gruber" in metrics["normalized_text"]

    def test_empty_transcript_handling(self) -> None:
        engine = MediaMindForgeEngine()
        metrics = engine.deconstruct_transcript("")

        assert metrics["word_count"] == 0
        assert metrics["duration_seconds"] == 0.0
        assert metrics["words_per_minute"] == 0.0
        assert len(metrics["segments"]) == 0


@pytest.mark.unit
class TestDualLensCognitiveMining:
    """Test Mind-Reader epistemic extraction and Forge procedural synthesis."""

    def test_extract_mental_models_and_heuristics(self) -> None:
        engine = MediaMindForgeEngine()
        report = engine.analyze(
            transcript_source=SAMPLE_RAW_TRANSCRIPT,
            skill_name="ontological-engineering-coach",
            author_or_speaker="Tom Gruber & Nicola Guarino",
            source_url="https://youtube.com/watch?v=sample",
            video_title="Ontological Engineering Masterclass",
        )

        assert report.status == "ok"
        assert report.skill_name == "ontological-engineering-coach"
        assert report.word_count > 100

        # Epistemic Mind-Reader outputs
        assert len(report.mental_models) >= 2
        model_names = [m.name for m in report.mental_models]
        assert any("Gruber" in name or "Ontolog" in name for name in model_names)

        assert len(report.decision_heuristics) >= 2
        assert any(h.rule_type in ("selection", "validation", "heuristic") for h in report.decision_heuristics)
        assert any(len(h.isnad_claims) > 0 for h in report.decision_heuristics)

        # Forge Procedural outputs
        assert len(report.procedural_stages) >= 3
        stage_names = [s.name for s in report.procedural_stages]
        assert any("Scoping" in name or "Taxonomy" in name for name in stage_names)
        assert all(len(s.completion_gate) > 0 for s in report.procedural_stages)

        # Anti-patterns
        assert len(report.anti_patterns) >= 2
        ap_names = [ap.name for ap in report.anti_patterns]
        assert any("Property" in name or "Taxonomic" in name or "Superficial" in name or "Speculative" in name for name in ap_names)

        # Diagnostic questions
        assert len(report.diagnostic_questions) >= 3

        # Knowledge Items
        assert len(report.knowledge_items) >= 2
        assert all(ki.source_type == "video_transcript" for ki in report.knowledge_items)
        assert all(len(ki.isnad_lineage) > 0 for ki in report.knowledge_items)

    def test_extract_with_timed_segments(self) -> None:
        engine = MediaMindForgeEngine()
        report = engine.analyze(
            transcript_source=SAMPLE_TIMED_SEGMENTS,
            skill_name="ontological-engineering-coach",
            video_title="Ontology Timed Lecture",
        )

        assert report.status == "ok"
        assert report.duration_seconds >= 43.5
        # Verify timestamped isnad claims
        all_isnad = []
        for h in report.decision_heuristics:
            all_isnad.extend(h.isnad_claims)
        for ki in report.knowledge_items:
            all_isnad.extend(ki.isnad_lineage)
        assert len(all_isnad) > 0


@pytest.mark.unit
class TestSkillAndBriefGeneration:
    """Test authoring of SKILL.md, CARD.md, and Visual Brief HTML."""

    def test_render_skill_md_conforms_to_rule_37(self) -> None:
        engine = MediaMindForgeEngine()
        report = engine.analyze(
            transcript_source=SAMPLE_RAW_TRANSCRIPT,
            skill_name="ontological-engineering-coach",
        )
        skill_md = engine.render_skill_md(report)

        # Rule 37 Invariant: SKILL.md must declare anti-patterns under an exact
        # ## Anti-Patterns heading containing list items formatted as - **Name** — Description
        assert "## Anti-Patterns" in skill_md
        assert "- **" in skill_md
        assert " — " in skill_md

        # Frontmatter presence
        assert skill_md.startswith("---\nname: ontological-engineering-coach")
        assert "description:" in skill_md

    def test_render_card_md_conforms_to_rule_37(self) -> None:
        engine = MediaMindForgeEngine()
        report = engine.analyze(
            transcript_source=SAMPLE_RAW_TRANSCRIPT,
            skill_name="ontological-engineering-coach",
        )
        card_md = engine.render_card_md(report)

        # Rule 37 Invariant: CARD.md metadata boxes must use standard single-pipe borders (│, not ║)
        assert "│ Name:        ontological-engineering-coach" in card_md or "│ Name:        " in card_md
        assert "│ Category:    " in card_md
        assert "│ Triggers:    " in card_md
        assert "║" not in card_md
        assert "│" in card_md
        assert "## Stage Progression Table" in card_md

    def test_render_visual_brief_html(self) -> None:
        engine = MediaMindForgeEngine()
        report = engine.analyze(
            transcript_source=SAMPLE_RAW_TRANSCRIPT,
            skill_name="ontological-engineering-coach",
        )
        html_path = engine.generate_visual_brief(report)

        assert Path(html_path).exists()
        content = Path(html_path).read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "mermaid" in content
        assert "Ontological Engineering" in content
        assert "Cognitive Topology DAG" in content


@pytest.mark.unit
class TestPluginLifecycleAndTools:
    """Test plugin registration into ServiceContext and tool functions."""

    def test_plugin_registration(self) -> None:
        plugin = MediaMindForgePlugin()
        assert "service.media_mind_forge" in plugin.manifest.provides
        assert plugin.manifest.name == "media_mind_forge"

        context = ServiceContext()
        plugin.register_services(context)

        # Verify resolution by typed ServiceKey per Rule 2
        service = context.require(MEDIA_MIND_FORGE_KEY)
        assert isinstance(service, MediaMindForgeService)
        assert service.engine is not None

    def test_tool_functions(self) -> None:
        # Health check
        h = health()
        assert h["status"] == "healthy"
        assert h["service"] == "media_mind_forge"

        # Full analyze tool
        res = media_mind_forge_analyze(
            transcript_source=SAMPLE_RAW_TRANSCRIPT,
            skill_name="ontological-engineering-coach",
        )
        assert res["status"] == "ok"
        assert "mental_models" in res
        assert "procedural_stages" in res

        # Distill KIs tool
        ki_res = media_mind_forge_distill_kis(
            transcript_source=SAMPLE_RAW_TRANSCRIPT,
            video_title="Ontology Lecture",
        )
        assert ki_res["status"] == "ok"
        assert ki_res["ki_count"] >= 2

        # Visual brief tool
        brief_res = media_mind_forge_visual_brief(
            transcript_source=SAMPLE_RAW_TRANSCRIPT,
            skill_name="ontological-engineering-coach",
        )
        assert brief_res["status"] == "ok"
        assert Path(brief_res["visual_brief_path"]).exists()

        # Craft skill tool with temp output dir
        with tempfile.TemporaryDirectory() as tmpdir:
            craft_res = media_mind_forge_craft_skill(
                transcript_source=SAMPLE_RAW_TRANSCRIPT,
                skill_name="ontological-coach-test",
                target_dir=tmpdir,
            )
            assert craft_res["status"] == "ok"
            assert (Path(craft_res["skill_dir"]) / "SKILL.md").exists()
            assert (Path(craft_res["skill_dir"]) / "CARD.md").exists()


@pytest.mark.integration
class TestSkillMetadataAndValidation:
    """Test validation reports and Agent Skill Knowledge Graph routing (Rules 34, 35, 37, 38)."""

    def test_skill_card_parser_plugin(self) -> None:
        plugin_dir = Path("plugins") / "memory_and_epistemics" / "media_mind_forge"
        node = SkillCardParser.parse_directory(plugin_dir)

        assert node is not None
        assert node.name == "media-mind-forge"
        assert node.category == "memory_and_epistemics"
        assert len(node.stages) >= 5
        assert len(node.anti_patterns) >= 2
        assert len(node.invariants) >= 3

    def test_skill_card_parser_agent_skill(self) -> None:
        skill_dir = Path(".agents") / "skills" / "media-mind-forge"
        node = SkillCardParser.parse_directory(skill_dir)

        assert node is not None
        assert node.name == "media-mind-forge"
        assert len(node.stages) >= 5
        assert len(node.anti_patterns) >= 2

    def test_skill_validator_passes(self) -> None:
        plugin_dir = Path("plugins") / "memory_and_epistemics" / "media_mind_forge"
        report = SkillValidator.validate(plugin_dir)

        # Rule 34 Invariant: evaluate overall boolean status via report.valid
        assert report.valid is True
        assert len(report.errors) == 0

    def test_plugin_validator_passes(self) -> None:
        plugin_dir = Path("plugins") / "memory_and_epistemics" / "media_mind_forge"
        # Rule 38 Invariant: invoke validate_sync to avoid unawaited coroutine error
        report = PluginValidator.validate_sync(plugin_dir)

        # Rule 34 Invariant: evaluate overall boolean status via report.valid
        assert report.valid is True
        assert len(report.errors) == 0

    def test_skill_knowledge_graph_routing(self) -> None:
        index_skill_catalog(".")

        # Query semantic intent to distill video transcript into skill and knowledge items
        res = query_skill_router("Distill video transcript and lecture into agent skills and knowledge items", top_k=3)
        assert res["status"] == "ok"
        assert len(res["matches"]) > 0

        # Rule 35 Invariant: match entries are strictly keyed by 'skill_name'
        match_names = [m["skill_name"] for m in res["matches"]]
        assert "media-mind-forge" in match_names
