```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        media-mind-forge                          │
│ Category:    memory_and_epistemics                     │
│ Invocation:  /media-mind-forge                         │
│ Triggers:    "analyze video transcript",               │
│              "learn from video", "distill lecture",    │
│              "forge skill from transcript"             │
│ Version:     1.0.0                                     │
│ Isolation:   in-process                                │
│ Provides:    "service.media_mind_forge"                │
├────────────────────────────────────────────────────────┤
│ Target:      Distill video transcripts into executable │
│              agent skills and grounded Knowledge Items.│
└────────────────────────────────────────────────────────┘
```

# Media Mind Forge — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Completion Gate |
|---|---|---|
| **1. Ingestion & Deconstruction** | Ingest transcript text or timed segments; compute metrics (words, duration, WPM) | `Transcript normalized` |
| **2. Dual-Lens Cognitive Mining** | Extract mental models, decision heuristics, arenaceous stages, isnad claims | `Models & stages extracted` |
| **3. Visual Brief Rendering** | Generate interactive dark-mode HTML report with Mermaid cognitive DAG in `%TEMP%` | `Visual brief generated` |
| **4. Checkpoint Gate** | Mandatory user verification of synthesized skill architecture and candidate KIs | `User checkpoint approved` |
| **5. Artifact Scaffolding & Commit** | Author validated `SKILL.md` and `CARD.md`; persist KIs with timestamped lineage | `Skill & KIs committed` |

---

## Input & Output Schema Specification

### Input Schema
| Field | Type | Required | Description |
|---|---|---|---|
| `transcript_source` | string \| list[object] | Yes | Raw dialogue string, file path, or timed segment array |
| `skill_name` | string | Optional | Target kebab-case identifier for forged skill |
| `author_or_speaker` | string | Optional | Primary speaker or author attribution |
| `source_url` | string | Optional | Original media / video URL for isnad lineage |
| `video_title` | string | Optional | Human-readable title of the media source |
| `target_dir` | string | Optional | Target directory for generated skill package |

### Output Schema
| Field | Type | Description |
|---|---|---|
| `status` | string | Execution outcome: `"ok"` or `"error"` |
| `skill_name` | string | Normalized identifier of synthesized skill |
| `word_count` | integer | Total processed words in transcript |
| `duration_seconds` | float | Total media duration |
| `words_per_minute` | float | Calculated speech tempo |
| `mental_models` | list[object] | First-principles, axioms, and trade-offs |
| `decision_heuristics` | list[object] | If-this-then-that operational heuristics |
| `diagnostic_questions`| list[object] | Diagnostic coaching interview rubric |
| `procedural_stages` | list[object] | Shu-Ha-Ri execution stages with gates |
| `knowledge_items` | list[object] | Distilled KIs formatted for Knowledge Vault |
| `visual_brief_path` | string | Path to generated HTML report in `%TEMP%` |

---

## Vocabulary & Cognitive Levers

- **Dual-Lens Extraction**: Simultaneous synthesis of epistemic axioms (`mind-reader`) and executable stages (`book-to-skill-forge`).
- **Epistemic Isnad Lineage**: Explicit citation chain binding every extracted mental model and heuristic to timestamped transcript segments.
- **Gruber-Guarino Ontological Commitment**: Axiomatic constraints defining entity definitions, boundary tests, and non-conflated taxonomy terms.
- **Shu-Ha-Ri Execution Stages**: Three-tier mastery progression structuring skills from strict conformance (Shu) to mastery divergence (Ri).
- **In-Flight Anti-Pattern Matrix**: Explicit catalog of negative behaviors, superficial summarization traps, and operational guardrails.

---

## Mandatory Invariants Checklist

- [ ] Metadata box strictly formatted with single-pipe (`│`) borders for `SkillCardParser` extraction
- [ ] Every extracted heuristic and mental model anchored to timestamped transcript quotes
- [ ] Interactive Visual Brief authored with self-contained CSS and embedded Mermaid SVG DAG
- [ ] Generated `SKILL.md` includes exact `## Anti-Patterns` heading with `- **Name** — Description` list items
- [ ] No persistent file writes or vault commits execute without passing mandatory checkpoint gate
