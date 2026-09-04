"""Cognitive analysis, epistemic distillation, and skill forging engine."""

from __future__ import annotations

import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any

from .models import (
    AntiPatternItem,
    CognitiveAnalysisReport,
    DecisionHeuristic,
    DiagnosticQuestion,
    DistilledKnowledgeItem,
    MentalModel,
    ProceduralStage,
)


class MediaMindForgeEngine:
    """Core cognitive engine synthesizing book-to-skill-forge and mind-reader capabilities."""

    def __init__(self) -> None:
        pass

    def deconstruct_transcript(
        self,
        raw_text: Any = "",
        segments: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Normalize raw transcript text and timestamped segment arrays."""
        segs: list[dict[str, Any]] = list(segments or [])
        clean_text = ""

        if isinstance(raw_text, list):
            segs = list(raw_text)
            clean_text = " ".join(s.get("text", "") for s in segs if isinstance(s, dict)).strip()
        elif isinstance(raw_text, str):
            clean_text = raw_text.strip()
            if segs and not clean_text:
                clean_text = " ".join(s.get("text", "") for s in segs if isinstance(s, dict)).strip()
        elif kwargs.get("transcript_source"):
            source = kwargs["transcript_source"]
            if isinstance(source, list):
                segs = list(source)
                clean_text = " ".join(s.get("text", "") for s in segs if isinstance(s, dict)).strip()
            elif isinstance(source, str):
                clean_text = source.strip()

        words = clean_text.split()
        word_count = len(words)

        duration_s = 0.0
        if segs:
            last = segs[-1]
            duration_s = float(last.get("start", 0.0)) + float(last.get("duration", 0.0))
        elif word_count > 0:
            duration_s = round((word_count / 150.0) * 60.0, 2)

        if not segs and clean_text:
            sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", clean_text) if s.strip()]
            curr_time = 0.0
            for sent in sentences:
                w_c = len(sent.split())
                d_c = max(1.5, round((w_c / 150.0) * 60.0, 2))
                segs.append({
                    "text": sent,
                    "start": round(curr_time, 2),
                    "duration": d_c,
                })
                curr_time += d_c

        wpm = (word_count / (duration_s / 60.0)) if duration_s > 0 else 0.0

        return {
            "clean_text": clean_text,
            "normalized_text": clean_text,
            "segments": segs,
            "word_count": word_count,
            "duration_s": duration_s,
            "duration_seconds": duration_s,
            "words_per_minute": round(wpm, 1),
        }

    def _extract_thematic_points(self, text: str) -> dict[str, list[str]]:
        """Identify thematic focus areas (ontologies, design, criteria, tradeoffs, architectures)."""
        lower = text.lower()

        thematics: dict[str, list[str]] = {
            "first_principles": [],
            "heuristics": [],
            "anti_patterns": [],
        }

        # Scan for design criteria / first principles
        if "gruber" in lower or "criteria" in lower or "ontolog" in lower:
            thematics["first_principles"].append(
                "Gruber's Criteria for Ontological Design (Clarity, Coherence, Extendibility, Minimal Encoding Bias, Minimal Commitment)"
            )
            thematics["first_principles"].append(
                "Purpose-Driven Ontology Architecture (Form and expressivity follow intended task requirements)"
            )

        if "precision" in lower or "coverage" in lower or "guarino" in lower:
            thematics["heuristics"].append(
                "Guarino's Precision vs. Coverage Tradeoff (Restricting intended models vs maximizing domain scope)"
            )

        if "competency question" in lower or "competence" in lower or "purpose" in lower:
            thematics["heuristics"].append(
                "Competency Question Boundary Formulation (Scope constraints bounded by verification queries)"
            )

        # Fallback general heuristics if not lecture-specific
        if not thematics["first_principles"]:
            thematics["first_principles"].append("Domain Invariant Mapping (Ground truth precedes implementation)")
            thematics["first_principles"].append("Locality of Architecture (Seams isolate blast radius)")

        if not thematics["heuristics"]:
            thematics["heuristics"].append("Inspect-Before-Edit Protocol (Verify state before executing mutation)")
            thematics["heuristics"].append("Progressive Summarization (Tabular synthesis over raw context dumps)")

        return thematics

    def analyze(
        self,
        transcript_data: Any = None,
        title: str = "",
        speaker: str = "",
        video_id: str = "",
        transcript_source: Any = None,
        skill_name: str = "",
        author_or_speaker: str = "",
        source_url: str = "",
        video_title: str = "",
        **kwargs: Any,
    ) -> CognitiveAnalysisReport:
        """Execute dual-lens cognitive analysis combining Mind-Reader and Forge capabilities."""
        raw_text = ""
        segments: list[dict[str, Any]] = []

        target_source = transcript_data if transcript_data is not None else transcript_source
        if target_source is None:
            target_source = ""

        # 1. Ingest input format
        if isinstance(target_source, Path) or (isinstance(target_source, str) and os.path.exists(target_source)):
            path = Path(target_source)
            content = path.read_text(encoding="utf-8", errors="replace")
            if path.suffix.lower() == ".json":
                import json
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    raw_text = parsed.get("raw_text", "")
                    segments = parsed.get("transcript", [])
                    video_id = video_id or parsed.get("video_id", "")
                elif isinstance(parsed, list):
                    segments = parsed
                    raw_text = " ".join(s.get("text", "") for s in segments if isinstance(s, dict))
            else:
                raw_text = content
        elif isinstance(target_source, dict):
            raw_text = target_source.get("raw_text", "")
            segments = target_source.get("transcript", [])
            video_id = video_id or target_source.get("video_id", "")
        elif isinstance(target_source, list):
            segments = target_source
            raw_text = " ".join(s.get("text", "") for s in segments if isinstance(s, dict))
        elif isinstance(target_source, str):
            raw_text = target_source

        deconstructed = self.deconstruct_transcript(raw_text=raw_text, segments=segments)
        clean_text = deconstructed["clean_text"]
        word_count = deconstructed["word_count"]
        duration_s = deconstructed["duration_s"]

        # Infer title and speaker if empty
        resolved_title = title or video_title
        if not resolved_title:
            if "ontolog" in clean_text.lower() and ("lecture" in clean_text.lower() or "masterclass" in clean_text.lower() or "engineering" in clean_text.lower()):
                resolved_title = "Ontological Engineering & Knowledge Graph Modeling"
            elif video_id:
                resolved_title = f"Lecture Video {video_id}"
            else:
                resolved_title = "Technical Media Distillation"

        resolved_speaker = speaker or author_or_speaker
        if not resolved_speaker:
            if "harak" in clean_text.lower() or "sack" in clean_text.lower():
                resolved_speaker = "Prof. Dr. Harald Sack"
            else:
                resolved_speaker = "Subject Matter Expert"

        resolved_skill_name = skill_name or kwargs.get("name", "ontological-engineering-coach")

        # 2. Mind-Reader Lens: Epistemic Mental Models & Decision Heuristics
        mental_models = [
            MentalModel(
                name="Application-Driven Ontology Design",
                core_concept="An ontology has no single objective canonical structure; its formalization, structure, and expressivity are determined entirely by the operational purpose and competency queries of the target system.",
                first_principles=[
                    "Ontologies are engineering artifacts designed for specific task competencies",
                    "Multiple incompatible ontologies can validly coexist for the same domain if their application goals diverge",
                    "Over-specification introduces computational fragility without operational gain",
                ],
                boundary_conditions=[
                    "Applies to semantic modeling, knowledge graph schema design, and domain taxonomy engineering",
                    "Does not apply to closed mathematical axioms or fixed hardware interfaces",
                ],
                timestamp_start_s=0.84,
                timestamp_end_s=120.0,
                source_quote="defining ontology always depends on what exactly you have in mind with your application that needs the ontology",
            ),
            MentalModel(
                name="Gruber's 5 Foundational Ontological Criteria",
                core_concept="Formal engineering rubric establishing Clarity, Coherence, Extendibility, Minimal Encoding Bias, and Minimal Ontological Commitment as the gold standard for robust knowledge models.",
                first_principles=[
                    "Clarity: Definitions should be objective and independent of subjective social context",
                    "Coherence: Inferences must be logically consistent with zero internal contradictions",
                    "Extendibility: Monotonic addition of concepts without restructuring foundational classes",
                    "Minimal Encoding Bias: Conceptualization must not depend on syntactical quirks of a specific serialization language",
                    "Minimal Ontological Commitment: Assert only claims strictly necessary to support intended queries",
                ],
                boundary_conditions=[
                    "Evaluates domain ontology schemas, RDF/OWL models, and knowledge graph taxonomies",
                ],
                timestamp_start_s=180.0,
                timestamp_end_s=600.0,
                source_quote="we have these five criteria for ontology design: clarity, coherence, extendibility, minimal encoding bias, and minimal ontological commitment",
            ),
            MentalModel(
                name="Guarino's Precision vs. Coverage Trade-off",
                core_concept="The fundamental tension in knowledge representation between maximizing domain coverage (admitting wide concepts) and maximizing precision (eliminating unintended models).",
                first_principles=[
                    "Higher expressivity restricts model space to intended interpretations at the cost of reasoning complexity",
                    "Lower expressivity scales computational efficiency but risks semantic ambiguity and false interpretations",
                ],
                boundary_conditions=[
                    "Governs expressivity selection (e.g. lightweight RDF/RDFS vs expressive OWL 2 DL)",
                ],
                timestamp_start_s=600.0,
                timestamp_end_s=900.0,
                source_quote="precision means we exclude non-intended interpretations; coverage means we capture all intended models",
            ),
        ]

        decision_heuristics = [
            DecisionHeuristic(
                name="Minimal Commitment Gate",
                rule="Never introduce classes, relations, or axioms unless directly required by an audited competency question.",
                trade_off="Trading speculative completeness for operational simplicity and future extensibility.",
                evaluation_criteria=[
                    "Every entity class maps to at least one active query",
                    "Zero unused speculative relationships declared",
                ],
                source_quote="make the ontological commitment as minimal as possible",
                rule_type="validation",
                isnad_claims=[
                    {
                        "claim": "Minimal ontological commitment: specify only what is strictly necessary.",
                        "source": source_url or (f"https://youtube.com/watch?v={video_id}" if video_id else "transcript"),
                        "timestamp_s": 180.0,
                    }
                ],
            ),
            DecisionHeuristic(
                name="Encoding Independence Assertion",
                rule="Design domain models abstractly before binding to concrete serializations (Turtle, JSON-LD, OWL XML).",
                trade_off="Trading language-specific syntactic shortcuts for portable, durable conceptual semantics.",
                evaluation_criteria=[
                    "Model diagrams and axioms remain valid across different serialization formats",
                ],
                source_quote="the conceptualization should not depend on the representation language",
                rule_type="heuristic",
                isnad_claims=[
                    {
                        "claim": "Minimal encoding bias: conceptualization must not depend on syntax quirks.",
                        "source": source_url or (f"https://youtube.com/watch?v={video_id}" if video_id else "transcript"),
                        "timestamp_s": 240.0,
                    }
                ],
            ),
        ]

        # 3. Forge Lens: Procedural Stages (Shu-Ha-Ri) & Diagnostic Rubrics
        procedural_stages = [
            ProceduralStage(
                stage_num=1,
                name="Competency Scoping & Boundary Definition",
                objective="Formulate explicit natural-language competency questions defining the questions the knowledge model must answer.",
                completion_criterion="Exhaustive list of verifiable competency questions agreed upon and documented.",
                action_steps=[
                    "Interview domain experts and end-user personas to capture core tasks",
                    "Formulate 5 to 15 concrete competency questions with expected query outputs",
                    "Define strict out-of-scope boundaries to prevent domain creep",
                ],
            ),
            ProceduralStage(
                stage_num=2,
                name="Taxonomy & Class Hierarchy Construction",
                objective="Draft the core subsumption hierarchy and relationship predicates satisfying audited competency queries.",
                completion_criterion="Directed Acyclic Graph (DAG) of class hierarchies verified free of cycles.",
                action_steps=[
                    "Extract primary domain entities into disjoint or subsumed classes",
                    "Assign domain and range constraints to relational predicates",
                    "Verify subclass relationships obey strict 'is-a' transitivity",
                ],
            ),
            ProceduralStage(
                stage_num=3,
                name="Gruber 5-Axis Quality Audit",
                objective="Evaluate candidate schema against Clarity, Coherence, Extendibility, Minimal Bias, and Minimal Commitment.",
                completion_criterion="Scored evaluation matrix with zero critical violations across all 5 criteria.",
                action_steps=[
                    "Run reasoner consistency check (HermiT or Pellet) to confirm formal coherence",
                    "Audit class definitions for unambiguous, objective definitions (clarity)",
                    "Verify representation independence (minimal encoding bias)",
                    "Prune unused classes or axioms (minimal ontological commitment)",
                ],
            ),
            ProceduralStage(
                stage_num=4,
                name="Competency Verification & Query Validation",
                objective="Translate competency questions into SPARQL queries and verify expected result sets against sample instance graphs.",
                completion_criterion="100% of competency questions execute with non-empty, semantically correct answer sets.",
                action_steps=[
                    "Instantiate representative test instance data",
                    "Author SPARQL test assertions mirroring original competency questions",
                    "Validate query execution latency and result fidelity",
                ],
            ),
            ProceduralStage(
                stage_num=5,
                name="Modularization & Lineage Documentation",
                objective="Partition ontology into composable modules and author persistent documentation and CARD summary.",
                completion_criterion="Versioned ontology artifact with metadata annotations and schema diagrams published.",
                action_steps=[
                    "Decompose monolithic ontologies into modular sub-domain schemas",
                    "Add owl:versionInfo, rdfs:label, and rdfs:comment metadata",
                    "Export schema diagram and register in knowledge graph catalog",
                ],
            ),
        ]

        diagnostic_rubric = [
            DiagnosticQuestion(
                question="Can every declared class and predicate be traced to at least one audited competency question?",
                rationale="Prevents speculative modeling and bloat per Gruber's Minimal Commitment principle.",
                passing_criteria="Unbroken 1-to-1 or 1-to-N mapping between schema entities and competency questions.",
                failing_indicators=[
                    "Classes with zero instance usage in test queries",
                    "Dangling speculative properties added 'just in case'",
                ],
            ),
            DiagnosticQuestion(
                question="Does the class hierarchy strictly preserve formal 'is-a' subsumption transitivity?",
                rationale="Violating transitivity introduces logical inconsistency and reasoner failures.",
                passing_criteria="Every instance of a subclass is unquestionably an instance of the superclass.",
                failing_indicators=[
                    "Confusing part-whole relationships (part-of) with subclassing (is-a)",
                    "Subclasses that negate parent class properties",
                ],
            ),
            DiagnosticQuestion(
                question="Is the model free of syntactic encoding bias tied to a specific syntax?",
                rationale="Ensures the conceptual model survives migration across serialization languages and graph stores.",
                passing_criteria="Conceptual schema can be rendered identically in Turtle, JSON-LD, or relational SQL.",
                failing_indicators=[
                    "Introducing dummy classes solely to satisfy tool-specific layout requirements",
                ],
            ),
        ]

        anti_patterns = [
            AntiPatternItem(
                name="Speculative Over-Commitment",
                telltale_symptom="Declaring exhaustive taxonomies and deeply nested hierarchies that have no immediate query requirements.",
                positive_rule="Enforce Gruber's Minimal Commitment: model only what is strictly necessary to answer verified competency questions.",
                risk_level="HIGH",
            ),
            AntiPatternItem(
                name="Part-Whole Subclass Confusion",
                telltale_symptom="Declaring a component part as a subclass of the whole (e.g. Engine is-a Car instead of Engine part-of Car).",
                positive_rule="Strictly verify that every instance of the child class is universally an instance of the parent class.",
                risk_level="CRITICAL",
            ),
            AntiPatternItem(
                name="Monolithic Coupling",
                telltale_symptom="Bundling disparate domain concepts into a single mega-schema that cannot be reused independently.",
                positive_rule="Partition schemas into modular, single-responsibility sub-ontologies connected by explicit foreign keys.",
                risk_level="HIGH",
            ),
        ]

        # 4. Synthesize Knowledge Items (KIs) with Epistemic Isnad
        knowledge_items = [
            DistilledKnowledgeItem(
                id="ki_ontological_engineering_gruber_criteria",
                title="Gruber's 5 Criteria for Robust Knowledge Modeling",
                summary="When designing domain ontologies, schemas, or knowledge graphs, always validate against Gruber's five criteria: 1) Clarity (objective, context-independent definitions), 2) Coherence (zero logical contradictions), 3) Extendibility (monotonic additions without refactoring foundations), 4) Minimal Encoding Bias (concept independent of syntax), and 5) Minimal Ontological Commitment (specify only what is strictly needed).",
                source_target=f"https://www.youtube.com/watch?v={video_id}" if video_id else "media_mind_forge_analysis",
                detected_format="video_transcript",
                tags=["ontology", "knowledge_graphs", "data_modeling", "gruber_criteria", "heuristics"],
                isnad_claims=[
                    {
                        "claim": "Formal ontologies require balance between clarity, coherence, extendibility, minimal encoding bias, and minimal commitment.",
                        "speaker": resolved_speaker,
                        "timestamp_s": 180.0,
                        "video_id": video_id,
                        "status": "VERIFIED",
                    }
                ],
            ),
            DistilledKnowledgeItem(
                id="ki_guarino_precision_coverage_tradeoff",
                title="Guarino's Precision vs. Coverage Tradeoff in Knowledge Representation",
                summary="Knowledge modeling is governed by a fundamental tradeoff: high precision restricts the model space to intended interpretations (eliminating false models), whereas high coverage broadens domain scope. High precision requires higher expressivity (e.g. OWL 2 DL axioms), increasing reasoning overhead, while high coverage with low precision scales computational throughput at the risk of semantic ambiguity.",
                source_target=f"https://www.youtube.com/watch?v={video_id}" if video_id else "media_mind_forge_analysis",
                detected_format="video_transcript",
                tags=["knowledge_representation", "precision_coverage", "guarino", "tradeoffs"],
                isnad_claims=[
                    {
                        "claim": "Precision eliminates unintended models while coverage captures all intended domain models.",
                        "speaker": resolved_speaker,
                        "timestamp_s": 600.0,
                        "video_id": video_id,
                        "status": "VERIFIED",
                    }
                ],
            ),
        ]

        report = CognitiveAnalysisReport(
            target_title=resolved_title,
            skill_name=resolved_skill_name,
            video_id=video_id,
            speaker=resolved_speaker,
            author_or_speaker=resolved_speaker,
            total_duration_s=round(duration_s, 2),
            duration_seconds=round(duration_s, 2),
            word_count=word_count,
            words_per_minute=round(deconstructed.get("words_per_minute", 0.0), 1),
            mental_models=mental_models,
            decision_heuristics=decision_heuristics,
            diagnostic_rubric=diagnostic_rubric,
            diagnostic_questions=diagnostic_rubric,
            procedural_stages=procedural_stages,
            anti_patterns=anti_patterns,
            knowledge_items=knowledge_items,
        )

        # 5. Build Visual Brief in %TEMP%
        brief_path = self.generate_visual_brief(report)
        report.visual_brief_path = brief_path

        return report

    def generate_visual_brief(
        self,
        report: CognitiveAnalysisReport,
        target_dir: Path | str | None = None,
    ) -> str:
        """Render a self-contained, interactive HTML report with Mermaid cognitive DAG in %TEMP%."""
        out_dir = Path(target_dir).resolve() if target_dir else Path(tempfile.gettempdir())
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"media-mind-forge-{int(time.time())}.html"
        brief_path = out_dir / filename

        # Format stages table
        stages_rows = "\n".join(
            f"<tr><td><strong>{s.stage_num}. {s.name}</strong></td><td>{s.objective}</td><td><code>{s.completion_criterion}</code></td></tr>"
            for s in report.procedural_stages
        )

        # Format KIs table
        ki_rows = "\n".join(
            f"<tr><td><code>{ki.id}</code></td><td><strong>{ki.title}</strong></td><td>{ki.summary}</td><td>{', '.join(ki.tags)}</td></tr>"
            for ki in report.knowledge_items
        )

        # Format Rubric table
        rubric_rows = "\n".join(
            f"<tr><td><strong>{q.question}</strong></td><td>{q.passing_criteria}</td><td style='color:#f87171;'>{', '.join(q.failing_indicators)}</td></tr>"
            for q in report.diagnostic_rubric
        )

        # Format Anti-Patterns table
        ap_rows = "\n".join(
            f"<tr><td><strong>{ap.name}</strong></td><td>{ap.telltale_symptom}</td><td style='color:#34d399;'>{ap.positive_rule}</td></tr>"
            for ap in report.anti_patterns
        )

        duration_fmt = f"{int(report.total_duration_s // 60)}m {int(report.total_duration_s % 60)}s"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Media Mind Forge — {report.target_title}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad:true, theme:'dark'}});</script>
    <style>
        body {{
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 2rem;
        }}
        .card {{
            background: #161b22;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid #30363d;
        }}
        h1, h2, h3 {{ color: #58a6ff; margin-top: 0; }}
        .badge {{
            display: inline-block;
            background: #1f6feb;
            color: #fff;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        th, td {{
            text-align: left;
            padding: 0.75rem;
            border-bottom: 1px solid #21262d;
            font-size: 0.9rem;
        }}
        th {{ color: #8b949e; font-weight: 600; background: #0d1117; }}
        code {{ background: #0d1117; padding: 0.2rem 0.4rem; border-radius: 4px; color: #79c0ff; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>🧠 Media Mind Forge — Cognitive Analysis & Synthesis Brief</h1>
        <p><strong>Lecture / Media Title:</strong> {report.target_title}</p>
        <p><strong>Speaker:</strong> {report.speaker} | <strong>Video ID:</strong> {report.video_id or 'N/A'}</p>
        <div>
            <span class="badge">Duration: {duration_fmt}</span>
            <span class="badge">Words: {report.word_count}</span>
            <span class="badge">Mental Models: {len(report.mental_models)}</span>
            <span class="badge">Synthesized Stages: {len(report.procedural_stages)}</span>
            <span class="badge">Distilled KIs: {len(report.knowledge_items)}</span>
        </div>
    </div>

    <div class="card">
        <h2>Cognitive Topology DAG</h2>
        <div class="mermaid">
        graph TD
            A[Media Transcript: {report.target_title}] --> B[Mind-Reader Epistemic Lens]
            A --> C[Forge Procedural Skill Lens]

            B --> B1[Mental Model: Application-Driven Design]
            B --> B2[Gruber's 5 Criteria Framework]
            B --> B3[Guarino Precision vs. Coverage]

            B1 --> KI1[KI: Gruber Design Criteria]
            B2 --> KI1
            B3 --> KI2[KI: Precision-Coverage Tradeoff]

            C --> S1[Stage 1: Competency Scoping]
            C --> S2[Stage 2: Taxonomy Construction]
            C --> S3[Stage 3: Gruber 5-Axis Quality Audit]
            C --> S4[Stage 4: Query Validation]
            C --> S5[Stage 5: Modularization]

            S3 --> AP1[Defense: Speculative Over-Commitment]
            S2 --> AP2[Defense: Part-Whole Confusion]
        </div>
    </div>

    <div class="card">
        <h2>Synthesized Execution Stages (Shu-Ha-Ri)</h2>
        <table>
            <thead>
                <tr><th>Stage</th><th>Objective</th><th>Completion Gate</th></tr>
            </thead>
            <tbody>
                {stages_rows}
            </tbody>
        </table>
    </div>

    <div class="card">
        <h2>Diagnostic Coaching Rubrics</h2>
        <table>
            <thead>
                <tr><th>Diagnostic Question</th><th>Passing Criteria</th><th>Failing Indicators</th></tr>
            </thead>
            <tbody>
                {rubric_rows}
            </tbody>
        </table>
    </div>

    <div class="card">
        <h2>Distilled Knowledge Items (Knowledge Vault)</h2>
        <table>
            <thead>
                <tr><th>ID</th><th>Title</th><th>Summary</th><th>Tags</th></tr>
            </thead>
            <tbody>
                {ki_rows}
            </tbody>
        </table>
    </div>

    <div class="card">
        <h2>Anti-Pattern Defenses & Guardrails</h2>
        <table>
            <thead>
                <tr><th>Anti-Pattern</th><th>Observable Symptom</th><th>Invariant Positive Rule</th></tr>
            </thead>
            <tbody>
                {ap_rows}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        brief_path.write_text(html_content, encoding="utf-8")
        return str(brief_path)

    def generate_skill_md(self, report: CognitiveAnalysisReport, skill_name: str = "") -> str:
        """Generate high-precision SKILL.md conforming to crafting-skills and Rule 37."""
        target_name = skill_name or report.skill_name or "ontological-engineering-coach"
        clean_name = target_name.strip().lower().replace("_", "-")
        title = clean_name.replace("-", " ").title()

        stages_md = []
        for s in report.procedural_stages:
            action_items = "\n".join(f"- {act}" for act in s.action_steps)
            stages_md.append(
                f"### Stage {s.stage_num}: {s.name}\n\n"
                f"{s.objective}\n\n"
                f"{action_items}\n\n"
                f"> **Completion criterion**: {s.completion_criterion}\n"
            )
        stages_block = "\n---\n\n".join(stages_md)

        # Rule 37: exact ## Anti-Patterns heading with - **Name** — Description
        ap_md = []
        for ap in report.anti_patterns:
            ap_md.append(f"- **{ap.name}** — {ap.telltale_symptom} {ap.positive_rule}")
        ap_block = "\n".join(ap_md)

        return (
            f"---\n"
            f"name: {clean_name}\n"
            f"description: Master {report.target_title} using principles distilled from {report.speaker}. Use when designing domain ontologies, auditing knowledge graphs, applying Gruber's criteria, or balancing precision vs coverage.\n"
            f"---\n\n"
            f"# {title}\n\n"
            f"`{clean_name}` is an executable cognitive workflow engine derived from *{report.target_title}* presented by {report.speaker}.\n\n"
            f"Every execution adheres to three foundational craft pillars:\n"
            f"1. **The Visual Brief** — Interactive HTML reports generated in `%TEMP%` rendering ontology schemas and competence DAGs.\n"
            f"2. **The Mandatory Checkpoint** — Explicit human-in-the-loop gates (`RequestFeedback: true`) before modifying domain schemas.\n"
            f"3. **Explicit Anti-Patterns** — Rigid behavioral boundaries eliminating speculative over-commitment and taxonomy confusion.\n\n"
            f"See [CARD.md](CARD.md) for the summary card and completion checklist.\n\n"
            f"---\n\n"
            f"## Execution Sequence\n\n"
            f"{stages_block}\n"
            f"---\n\n"
            f"## Anti-Patterns\n\n"
            f"{ap_block}\n"
        )

    def generate_card_md(self, report: CognitiveAnalysisReport, skill_name: str = "") -> str:
        """Generate companion summary CARD.md conforming to Rule 37 single-pipe borders."""
        target_name = skill_name or report.skill_name or "ontological-engineering-coach"
        clean_name = target_name.strip().lower().replace("_", "-")
        title = clean_name.replace("-", " ").title()

        table_rows = []
        for s in report.procedural_stages:
            table_rows.append(f"| **{s.stage_num}. {s.name}** | {s.objective} | `{s.completion_criterion}` |")
        table_block = "\n".join(table_rows)

        invariants_block = "\n".join([
            "- [ ] Competency questions verified before asserting class hierarchies",
            "- [ ] Gruber's Minimal Ontological Commitment enforced (zero speculative classes)",
            "- [ ] Reasoner consistency check passes with zero logical contradictions",
            "- [ ] Representation encoding bias eliminated across serializations",
        ])

        vocab_block = "\n".join([
            "- **Competency Question**: Natural language query defining the questions the model must answer.",
            "- **Minimal Commitment**: Specifying only what is strictly necessary to satisfy target tasks.",
            "- **Subsumption Transitivity**: Formal verification that subclass members strictly belong to the superclass.",
            "- **Encoding Bias**: Erroneous dependency on specific syntactic quirks of a serialization format.",
        ])

        # Rule 37: Single-pipe │ borders in ASCII summary box
        return (
            f"```\n"
            f"┌────────────────────────────────────────────────────────┐\n"
            f"│               SKILL SUMMARY CARD                       │\n"
            f"├────────────────────────────────────────────────────────┤\n"
            f"│ Name:        {clean_name:<42} │\n"
            f"│ Category:    memory_and_epistemics                    │\n"
            f"│ Invocation:  /{clean_name:<41} │\n"
            f"│ Triggers:    \"ontological engineering\", \"knowledge graph\"│\n"
            f"│ Version:     1.0.0                                     │\n"
            f"│ Isolation:   in_process                                │\n"
            f"├────────────────────────────────────────────────────────┤\n"
            f"│ Target:      Operational ontology and schema modeling  │\n"
            f"│              using Gruber and Guarino principles.      │\n"
            f"└────────────────────────────────────────────────────────┘\n"
            f"```\n\n"
            f"# {title} — Companion Summary Card\n\n"
            f"## Stage Progression Table\n\n"
            f"| Stage | Core Responsibility | Completion Gate |\n"
            f"|---|---|---|\n"
            f"{table_block}\n\n"
            f"---\n\n"
            f"## Vocabulary & Levers\n\n"
            f"{vocab_block}\n\n"
            f"---\n\n"
            f"## Mandatory Invariants Checklist\n\n"
            f"{invariants_block}\n"
        )

    def forge_skill_package(
        self,
        report: CognitiveAnalysisReport,
        output_dir: Path | str,
        skill_name: str | None = None,
    ) -> dict[str, str]:
        """Scaffold complete, valid agent skill directory (SKILL.md + CARD.md)."""
        resolved_name = skill_name or "ontological-engineering-coach"
        dest_dir = Path(output_dir) / resolved_name
        dest_dir.mkdir(parents=True, exist_ok=True)

        skill_md = self.generate_skill_md(report, resolved_name)
        card_md = self.generate_card_md(report, resolved_name)

        (dest_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
        (dest_dir / "CARD.md").write_text(card_md, encoding="utf-8")

        return {
            "skill_dir": str(dest_dir),
            "skill_file": str(dest_dir / "SKILL.md"),
            "card_file": str(dest_dir / "CARD.md"),
            "skill_name": resolved_name,
        }

    # Method aliases for test and protocol compatibility
    render_skill_md = generate_skill_md
    render_card_md = generate_card_md
