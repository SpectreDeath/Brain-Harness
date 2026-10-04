# Stage-Pillar Heading Disambiguation in Markdown AST Parsers

## Problem
In autonomous agent skill authoring, `SKILL.md` specifications must satisfy two competing structural requirements:
1. Declare sequential execution stages via numbered markdown headings (`## 1. Stage Name` or `### 1. Stage Name`).
2. Declare the three foundational craft pillars: Visual Brief, Mandatory Checkpoint, and Anti-Patterns.

`SkillCardParser._extract_stages_from_skill_md` uses a multiline regular expression:
```python
stage_pattern = re.compile(r"^(?:##|###)\s+(\d+)\.\s+(.+)$", re.MULTILINE)
```
If the craft pillars are formatted using Arabic numerals (e.g. `### 1. The Visual Brief`, `### 2. The Mandatory Checkpoint`, `### 3. Explicit Anti-Patterns`), `SkillCardParser` captures them as Stages 1, 2, and 3, inflating the skill's stage count from 5 to 8 and breaking pipeline validation.

## Solution
Format foundational skill pillars using Roman numeral styling:
```markdown
## The Three Foundational Pillars

### Pillar I: The Visual Brief
...

### Pillar II: The Mandatory Checkpoint
...

### Pillar III: Explicit Anti-Patterns
...
```

This formatting:
- Eliminates regex match in `stage_pattern` because `Pillar I:` does not match `\d+\.`.
- Preserves 100% compliance with `SkillPillarRule` which checks `re.search(r"##.*Visual Brief|###.*Visual Brief|The Visual Brief|%TEMP%", ...)` and `re.search(r"##.*Checkpoint|###.*Checkpoint|...", ...)`.
- Guarantees strict 1:1 parity between declared execution stages in `SKILL.md` and the stage table in `CARD.md`.

## Provenance
- `src/harness/services/skill_parser.py#L338-L380`
- `src/harness/creator/skills.py#L416-L442`
- `.agents/skills/brain-artifact-miner/SKILL.md`
- `tests/test_brain_artifact_miner.py`
