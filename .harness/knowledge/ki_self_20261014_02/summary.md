# Markdown Document Structural Formatting and Unified Unordered List Hygiene

## Epistemic Introspection & Root Cause Analysis

In multi-agent and automated documentation systems, markdown files frequently accumulate lint warnings due to subtle structural irregularities:
1. **Heading Adjacency (MD022 & MD032)**: Placing list items immediately under heading tags (`### Heading\n* Item`) violates Markdownlint rules requiring surrounding blank lines (`### Heading\n\n* Item`).
2. **Marker Style Polymorphism (MD004)**: Mixing asterisk markers (`* **Scope**:`) with hyphen markers (`  - item`) across nested or parallel lists triggers document-wide unordered list style conflicts.
3. **Multi-Line Whitespace Gaps (MD012)**: Repeated blank lines (`\n\n\n`) between sections trigger lint failures and bloat context window payloads.

## Actionable Invariant & Architectural Standard

1. **Enforce Uniform Dash Bullets**: Use hyphens (`-`) exclusively for all unordered list items at all indentation levels across the repository (`CONTEXT-MAP.md`, `CARD.md`, `SKILL.md`).
2. **Mandatory Heading Surrounding Blanks**: Ensure every markdown heading (`#`, `##`, `###`) is preceded and succeeded by exactly one blank line.
3. **Collapse Multi-Line Blank Gaps**: Never allow more than one consecutive blank line in markdown documentation suites.
4. **Validate Against AST Parsers**: Ensure structural formatting changes do not break downstream parsers (such as `SkillCardParser` or contract tests searching for specific markdown anchors).

## Grounded Evidence & Isnād Lineage

- **Primary Commit**: `6e43ba7` (`fix(skills): consolidate deepen_cycle.py to single-file <=190 LOC and standardize CONTEXT-MAP.md markdown`).
- **Empirical Result**: Cleared 45+ MD004, MD012, MD022, and MD032 warnings in `CONTEXT-MAP.md` while maintaining 100% test contract passing.
