# KI: Monorepo Golden-Copy Multi-Channel Distribution & ClawHub Slug Optimization

## Operational Summary
Maintaining dozens of agent skills across diverse packaging standards (ClawHub, Open Plugins for Cursor/Claude Code, npx CLI, and npm packages) causes documentation drift and search friction. Centralizing golden copies in a monorepo and utilizing deterministic keyword slugs (`<action-noun>-cellcog`) guarantees instant agent discovery and zero-drift releases.

## Architecture & Taxonomy Invariants

1. **Monorepo Golden Copy & Automated Compilation**:
   - Golden skill definitions reside in `monorepo/md/cellcog/openclaw_skills/`.
   - `skills-main/` (skills.sh / ClawHub) receives pure copy + validation across all 39 skills.
   - `cellcog-plugin-main/` receives a curated subset of 16 modality skills with ClawHub-specific YAML frontmatter stripped, compiling cleanly against the Open Plugins specification (`.cursor-plugin/`, `.claude-plugin/`, `.plugin/`).

2. **Literal Keyword Slug Migration (`<keyword-phrase>-cellcog`)**:
   - Short/branded slugs (e.g. `video-cog`, `slides-cog`, `story-cog`) were systematically migrated to full semantic keyword slugs (`video-generation-cellcog`, `presentation-slides-cellcog`, `creative-writing-cellcog`).
   - Rationale: AI agent discovery engines and ClawHub search algorithms perform token-first matching against folder names and frontmatter `name:` fields. Leading with literal capability terms drastically increases zero-shot skill discovery rates.

3. **CI Drift Gate (`sync_skills.py --check`)**:
   - Automated CI scripts enforce directory-name == frontmatter-name parity, non-empty descriptions, and universal `npx` install instructions, exiting with error code `1` upon any detected file deviation.

## Key References
- Sync Script: [`skills-main/skills-main/scripts/sync_skills.py`](file:///D:/GitHub/cloned/CellCog/skills-main/skills-main/scripts/sync_skills.py#L1-L100)
- Plugin Manifest: [`cellcog-plugin-main/cellcog-plugin-main/package.json`](file:///D:/GitHub/cloned/CellCog/cellcog-plugin-main/cellcog-plugin-main/package.json#L20-L50)
- Changelog History: [`cellcog-plugin-main/cellcog-plugin-main/CHANGELOG.md`](file:///D:/GitHub/cloned/CellCog/cellcog-plugin-main/cellcog-plugin-main/CHANGELOG.md#L1-L80)
- Visual Brief: [repo-reader-20260831-110000.html](file:///C:/Users/spectre/AppData/Local/Temp/repo-reader-20260831-110000.html)
