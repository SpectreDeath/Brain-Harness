# Skill Knowledge Graph Parser & ASCII Single-Pipe Card Formatting

**ID:** `ki_self_20260905_03`  
**Category:** `skill_engineering`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `plugins/memory_and_epistemics/skill_knowledge_graph/parser.py`, `tests/test_youtube_transcript_fetcher.py#L283`, `commit#fb9ffb6`, `AGENTS.md#Rule37`

## Executive Summary
The Skill Knowledge Graph metadata extractor (`SkillCardParser._extract_ascii_card()`) uses targeted regular expressions to strip border characters when parsing companion `CARD.md` files. When authoring companion cards, the header ASCII box must use standard single-pipe borders (`│`, not `║`). Using double-pipe borders breaks boundary capture, causing metadata extraction to silently fall back to the default category `"general"`.

## Architectural Invariants & Rules
1. **Single-Pipe Border Invariant**: All companion `CARD.md` metadata header boxes must use single-pipe borders (`│`) to ensure deterministic field extraction for `Name:`, `Category:`, and `Triggers:`.
2. **Anti-Patterns Heading & Format**: In `SKILL.md`, anti-patterns must be declared under an exact `## Anti-Patterns` heading with list items formatted as `- **Name** — Description`.
3. **Semantic Router Reliability**: Adhering to these strict card formatting invariants guarantees that graph routing (`query_skill_router()`) correctly indexes categories and triggers.
4. **Codification**: Formally codified as `AGENTS.md` Rule 37.
