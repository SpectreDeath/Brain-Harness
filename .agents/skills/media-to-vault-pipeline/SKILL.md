---
name: media-to-vault-pipeline
description: Extract video dialogue, distill factual claims and procedural workflows, verify isnad provenance, and scaffold verified skills and Knowledge Items. Do not use for general video editing or entertainment media.
---

# Media to Vault Pipeline: Multimedia Transcript to Verified Skill

`media-to-vault-pipeline` automates the end-to-end operational workflow for extracting spoken audio dialogue from YouTube and technical videos, executing dual-lens cognitive distillation (Rule 41), validating isnad claim provenance, committing canonical dual-file Knowledge Items (Rule 40), and scaffolding production agent skills.

## Dependencies

This workflow coordinates and reuses the following core skills:
- [`youtube-transcript-fetcher`](../youtube-transcript-fetcher/SKILL.md): Extracts timestamped dialogue and captions via isolated subprocess.
- [`multimedia-intelligence-forge`](../multimedia-intelligence-forge/SKILL.md): Executes deep audio/video extraction pipelines.
- [`media-mind-forge`](../media-mind-forge/SKILL.md): Unifies literature distillation with introspective reflection.
- [`epistemic-isnad-audit`](../epistemic-isnad-audit/SKILL.md): Verifies unbroken provenance chains for factual claims.
- [`deep-skill-forge`](../deep-skill-forge/SKILL.md): Scaffolds slotted domain skills from distilled literature.
- [`agent-skill-sdlc`](../agent-skill-sdlc/SKILL.md): Enforces schema validation and zero-fork configurations.

## Quick Start

```bash
# Option A: One-Shot Composite Pipeline Execution (Recommended)
python .agents/skills/media-to-vault-pipeline/scripts/media_pipeline_cli.py run --source "https://www.youtube.com/watch?v=EXAMPLE" --ki-id "ki_video_distill_01" --skill-name "sample-domain-skill" --output %TEMP%/pipeline_report.json

# Option B: Granular Multi-Step Execution
# 1. Fetch transcript from YouTube video URL or local file
python .agents/skills/media-to-vault-pipeline/scripts/media_pipeline_cli.py fetch-transcript --source "https://www.youtube.com/watch?v=EXAMPLE" --output %TEMP%/raw_transcript.json

# 2. Distill into dual-lens seams (epistemic claims vs procedural steps)
python .agents/skills/media-to-vault-pipeline/scripts/media_pipeline_cli.py distill-seams --transcript %TEMP%/raw_transcript.json --output %TEMP%/distilled_seams.json

# 3. Verify isnad chain-of-custody for extracted claims
python .agents/skills/media-to-vault-pipeline/scripts/media_pipeline_cli.py verify-isnad --distilled %TEMP%/distilled_seams.json --output %TEMP%/isnad_ledger.json

# 4. Commit to canonical Knowledge Vault (.harness/knowledge/<ki_id>/)
python .agents/skills/media-to-vault-pipeline/scripts/media_pipeline_cli.py commit-vault --ki-id "ki_video_distill_01" --distilled %TEMP%/distilled_seams.json --output %TEMP%/vault_commit.json

# 5. Scaffold production agent skill
python .agents/skills/media-to-vault-pipeline/scripts/media_pipeline_cli.py scaffold-skill --skill-name "sample-domain-skill" --distilled %TEMP%/distilled_seams.json --output %TEMP%/skill_scaffold.json
```

## Utility Scripts

The companion CLI script `scripts/media_pipeline_cli.py` delegates to `media_pipeline_engine.py` and implements both composite and modular subcommands:

- `run`: Executes the complete media-to-vault pipeline in a single atomic call with isnad validation and canonical dual-file vault commitment.
- `fetch-transcript`: Connects to `youtube-transcript-fetcher` or reads local transcripts, outputting timed segments and dialogue to `--output <file.json>`.
- `distill-seams`: Partitions unstructured media into Seam 1 (Epistemic Ground Truth) and Seam 2 (Procedural Agent Capabilities) per Rule 41.
- `verify-isnad`: Validates claim citations against video timestamp anchors, computing confidence scores.
- `commit-vault`: Persists canonical dual-file Knowledge Items (`metadata.json` + `summary.md`) under `.harness/knowledge/<ki_id>/` per Rule 40.
- `scaffold-skill`: Generates slotted, frozen skill models (`SKILL.md`, `CARD.md`, `config.default.yaml`) adhering to Rule 37 & 44.

## Workflow Stages

### Stage 1: Transcript Ingestion
Extract full spoken dialogue, speaker segments, and video timestamps using `youtube-transcript-fetcher` with automated exponential backoff on transient errors.
> **Completion criterion**: Comprehensive timed dialogue JSON written to output with zero truncated segments.

### Stage 2: Dual-Lens Cognitive Distillation
Bifurcate raw transcript data across the two foundational seams: epistemic principles (facts, mental models) and procedural rules (actions, decision trees) per Rule 41.
> **Completion criterion**: Structured JSON containing partitioned claims and actionable procedural rubrics.

### Stage 3: Isnad Provenance Verification
Verify unbroken chain-of-custody for each extracted claim against source timestamps or literature references using `epistemic-isnad-audit`.
> **Completion criterion**: All claims achieve $\ge 0.85$ isnad confidence with timestamp anchors verified.

### Stage 4: Mandatory Checkpoint
Generate an interactive HTML visual brief summarizing extracted knowledge items and proposed skill architectures. Await explicit user confirmation before modifying persistent state.
> **Completion criterion**: Explicit user confirmation received before committing to Knowledge Vault or scaffolding skills.

### Stage 5: Vault Commit & Skill Scaffolding
Persist canonical dual-file directories under `.harness/knowledge/<ki_id>/` (Rule 40) and scaffold compliant agent skills under `.agents/skills/<name>/` (Rule 44).
> **Completion criterion**: Validated Knowledge Item committed and compliant agent skill registered with zero linter errors.

## Visual Brief

When transcript distillation completes, generate an interactive HTML visual brief at `%TEMP%/media-vault-review-<timestamp>.html` rendering the dual-lens seam diagram, claim isnad lineage, and preview cards.

## Rate Limiting

The CLI script implements built-in rate limiting (default 2 requests per second) with file-lock synchronization and exponential backoff on HTTP 429 errors to prevent API quota exhaustion during batch ingestion.

## Anti-Patterns

- **Single Flat Knowledge Dump** — Dumping flat JSON arrays directly into `.harness/knowledge/` instead of the canonical dual-file directory format (Rule 40).
- **Unverified Isnad Claims** — Promoting extracted statements into persistent memory without timestamp anchors or source citations.
- **Unpartitioned Transcript Bloat** — Generating agent skills directly from raw dialogue without bifurcating epistemic ground truth from procedural action rubrics (Rule 41).
- **Bypassing Visual Brief Checkpoint** — Creating persistent skills or modifying the vault without user review of extracted claims.
