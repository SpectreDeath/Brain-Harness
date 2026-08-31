# Epistemic Habit — Skill SKILL.md as Design Contract

## Problem
Architectural decisions are scattered across conversations, code comments, and PR descriptions. When revisiting a system, the original rationale is lost or buried.

## Solution
Treat each skill's SKILL.md as the authoritative design contract:
- Encode trigger bounds, anti-patterns, and completion criteria in SKILL.md.
- Update SKILL.md before changing implementation code.
- Use CARD.md for machine-readable summaries that agents can route on.

## Operational Guideline
Before modifying any plugin or skill behavior, read its SKILL.md. If the behavior change is not reflected in SKILL.md, the change is incomplete. SKILL.md revisions are not optional documentation—they are the specification.

## Provenance
- Source brain: `antigravity_core`
- Primary source: `c5505b1b-eed6-40d3-b07d-0e060e559d5f.system_generated/logs/transcript_full.jsonl#L37`
- Distilled from: mind-reader skill creation, codebase-design skill viewing sessions