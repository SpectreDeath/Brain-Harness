# plugin.media_mind_forge (v1.0.0)

Cognitive analysis, epistemic distillation, and skill forging engine combining book-to-skill-forge and mind-reader

---

## Overview & Metadata

- **Plugin Directory**: `plugins/memory_and_epistemics/media_mind_forge`
- **Isolation Mode**: `in_process`
- **Services Provided**: `service.media_mind_forge`
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `media_mind_forge_analyze` | `(transcript, file_path, video_url, video_id, title, speaker)` | Execute dual-lens cognitive analysis combining mind-reader and book-to-skill-forge on video transcripts |
| `media_mind_forge_distill_kis` | `(transcript, file_path, video_url, video_id, persist_to_storage)` | Extract Knowledge Items (KIs) with epistemic isnad chains from video transcripts |
| `media_mind_forge_craft_skill` | `(transcript, file_path, video_url, video_id, skill_name, output_dir)` | Synthesize complete, validated agent skill package (SKILL.md + CARD.md) from media transcript |
| `media_mind_forge_visual_brief` | `(transcript, file_path, video_url, video_id)` | Generate self-contained HTML visual brief report in %TEMP% with Mermaid cognitive topology |
---

## Key Modules & AST Symbols

### Package [`engine/`](engine/)

Cognitive analysis, epistemic distillation, and skill forging engine decomposed into domain-partitioned submodules:

- [`engine/models.py`](engine/models.py): Slotted/frozen internal representations (`DeconstructedTranscriptResult`, `IsnadClaimNode`, `ThematicPoints`, `SkillPackageResult`).
- [`engine/transcripts.py`](engine/transcripts.py): Transcript normalization, timeline segmentation, and speaking pace (WPM) metrics.
- [`engine/distillation.py`](engine/distillation.py): Mind-Reader epistemic lens for mental models, decision heuristics, and isnād provenance attribution.
- [`engine/procedures.py`](engine/procedures.py): Forge procedural lens for Shu-Ha-Ri execution stages, diagnostic scorecards, and anti-pattern items.
- [`engine/brief.py`](engine/brief.py): Interactive HTML visual brief generator with embedded Mermaid DAG and metrics badges in `%TEMP%`.
- [`engine/scaffolder.py`](engine/scaffolder.py): High-precision `SKILL.md` (Rule 37) and `CARD.md` (single-pipe borders per Rule 37) scaffolding.
- [`engine/core.py`](engine/core.py): Slotted coordinator class `MediaMindForgeEngine` unifying all domain pipelines.
- [`engine/__init__.py`](engine/__init__.py): Subpackage facade re-exporting all domain symbols with 100% backward compatibility.


### Module [`main.py`](main.py)

Media Mind Forge Plugin — Cognitive Analysis, Epistemic Distillation, and Skill Synthesis.

#### Classes

- `class MediaMindForgeService`
  Authoritative service protocol for Media Mind Forge cognitive distillation.
  - `def analyze_media(transcript_data, title, speaker, video_id) -> CognitiveAnalysisReport`
  - `def distill_knowledge_items(transcript_data, video_id) -> list[dict[str, Any]]`
  - `def craft_skill(transcript_data, skill_name, output_dir) -> dict[str, str]`
- `class MediaMindForgePlugin`
  Brain-Harness plugin synthesizing book-to-skill-forge and mind-reader for media.
  - `def __init__(engine) -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def manifest() -> Any`
  - `def register_services(ctx) -> None`
  - `def on_load(ctx) -> None`
  - `def analyze_media(transcript_data, title, speaker, video_id) -> CognitiveAnalysisReport`
  - `def distill_knowledge_items(transcript_data, video_id) -> list[dict[str, Any]]`
  - `def craft_skill(transcript_data, skill_name, output_dir) -> dict[str, str]`


#### Functions

- `def media_mind_forge_analyze(transcript, file_path, video_url, video_id, title, speaker) -> dict[str, Any]`
  - Execute dual-lens cognitive analysis combining mind-reader and book-to-skill-forge.
- `def media_mind_forge_distill_kis(transcript, file_path, video_url, video_id, persist_to_storage) -> dict[str, Any]`
  - Extract Knowledge Items (KIs) with epistemic isnad chains from media transcript.
- `def media_mind_forge_craft_skill(transcript, file_path, video_url, video_id, skill_name, output_dir) -> dict[str, Any]`
  - Synthesize complete, validated agent skill package (SKILL.md + CARD.md) from media.
- `def media_mind_forge_visual_brief(transcript, file_path, video_url, video_id) -> dict[str, Any]`
  - Generate self-contained HTML visual brief report in %TEMP%.
- `def health() -> dict[str, Any]`
  - Return runtime health status for Media Mind Forge plugin.


### Module [`models.py`](models.py)

Data models for Media Mind Forge cognitive analysis and distillation.

#### Classes

- `class MentalModel`
  Ground-truth conceptual model or first principle extracted from media.
- `class DecisionHeuristic`
  Operational rule of thumb or decision tradeoff extracted from media.
- `class DiagnosticQuestion`
  Author's diagnostic coaching probe to evaluate work against domain standards.
- `class ProceduralStage`
  Concrete Shu-Ha-Ri execution stage with verifiable completion gate.
  - `def model_post_init(__context) -> None`
- `class AntiPatternItem`
  Named failure mode paired with an invariant behavioral defense.
- `class DistilledKnowledgeItem`
  Ground-truth Knowledge Item (KI) formatted for the Harness Knowledge Vault.
  - `def model_post_init(__context) -> None`
- `class CognitiveAnalysisReport`
  Consolidated dual-lens cognitive analysis payload.
  - `def model_post_init(__context) -> None`



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
