# SkillCardParser Grammar: Single-Key `CARD.md` Lines & Numbered Stages

## Failure Modes Observed
1. Placing two metadata fields on one ASCII box row in `CARD.md` (`│ Domain: agent_orchestration            Upstream: ... │`) caused `skills index --json` to ingest trailing columns verbatim as a polluted category name.
2. Using a numbered list inside `## The Three Foundational Pillars` instead of numbered top-level Markdown headings (`## 1. ...`, `## 2. ...`, `## 3. ...`) left `SkillCardParser.stages == []`, failing `tests/test_skills_hygiene.py::TestSkillsEcosystemHygiene::test_all_skills_parser_and_pillars`.

## Mandatory Invariant
- Keep exactly one `Key: Value` field per line inside `CARD.md` ````ascii` metadata boxes (`Category:`, `Version:`, `Invocation:`, `Triggers:`, `Requires:`, `Target:`).
- Always include at least 2 numbered workflow stage headings (`## 1. ...`, `## 2. ...`) in `SKILL.md`, and verify with both `harness.cli skills index --json` and `tests/test_skills_hygiene.py`.
