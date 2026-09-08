## BuiltinSkillRegistry Dual-Parser Divergence Gap

### Problem
`BuiltinSkillRegistryService._parse_skill_dir()` in `src/harness/services/skill_graph.py` 
lines 342-422 maintains its own shallow regex parser that:
- Ignores ASCII box borders in `CARD.md` files
- Leaves `invariants`, `triggers`, and `blocking_checklist` fields empty for all 42 skills
- Duplicates logic already implemented correctly in `SkillCardParser`
- Results in `harness skills graph` reporting empty blocking lists and invariant sets

This is a leaky abstraction that silently provides inferior skill metadata to the harness 
knowledge graph and router, causing skill routing mismatches.

### Fix
Refactor `BuiltinSkillRegistryService._parse_skill_dir()` to delegate card parsing to 
the canonical `SkillCardParser`:

```python
from harness.creator.validator import SkillCardParser

def _parse_skill_dir(self, path: Path) -> SkillEntry | None:
    card_path = path / "CARD.md"
    if card_path.exists():
        parsed = SkillCardParser(card_path).parse()
        return SkillEntry(
            name=parsed.name,
            invariants=parsed.invariants,
            triggers=parsed.triggers,
            blocking_checklist=parsed.blocking_checklist,
        )
    ...
```

### Impact
All 42 skills immediately gain full ASCII metadata, invariant visibility, and trigger 
matching — zero new code, pure delegation.

### Evidence
- architecture-review-20260908_063207.html: Candidate 2, rated STRONG
- src/harness/services/skill_graph.py:L342-L422 (shallow regex block)
