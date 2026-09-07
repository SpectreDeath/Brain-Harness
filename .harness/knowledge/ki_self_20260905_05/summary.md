# Skill Card ASCII Header Tagging & Zero-Warning Platform Compliance

**ID:** `ki_self_20260905_05`  
**Category:** `skill_architecture`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `src/harness/creator/skills.py#L464`, `.agents/skills/agent-skill-sdlc/CARD.md`, `AGENTS.md#Rule37`, `architecture-review-1788636271.html`

## Executive Summary
In `src/harness/creator/skills.py`, the `SkillCardRule` verification logic checks:
```python
has_ascii = "╔" in card_text or "==" in card_text or "SKILL:" in card_text
```
Concurrently, `AGENTS.md` Rule 37 mandates standard single-pipe borders (`│`, not `║`) to ensure that `SkillCardParser._extract_ascii_card()` cleanly strips delimiters when extracting `Name:`, `Category:`, and `Triggers:`. 

When skill authors use single-pipe borders (`│`) without explicitly including `"SKILL:"` or `"=="`, `harness skills validate` emits:
`Warning: CARD.md missing stage table or ASCII card box`
even though the box visually exists.

## Architectural Solution & Invariant
Including the tag `SKILL: <skill-name>` directly inside the ASCII box header:
```text
┌────────────────────────────────────────────────────────┐
│               SKILL: <skill-name>                      │
├────────────────────────────────────────────────────────┤
```
satisfies both constraints simultaneously:
1. `SkillCardParser` strips standard single-pipe borders (`│`) without string delimiter collisions.
2. `SkillCardRule` detects `"SKILL:" in card_text` and validates the ASCII header box.
3. The platform validator produces a clean **Overall Status: ✓ PASS** with zero warnings and zero errors.

Codified in `AGENTS.md` as Rule 37.
