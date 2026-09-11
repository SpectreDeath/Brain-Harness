## Markdown AST Codeblock Stripping & Skill Link Portability Invariant

### Problem
Static analysis linters and documentation checkers parsing markdown documents via line-based regexes frequently suffer false-positive failures:
1. **Codeblock Bleed**: Illustrative code blocks containing file paths, markdown link examples (e.g. `[link](file:///...)`), or commented headings (`# comments`) bleed into structural checks and trigger broken link or invalid stage count errors.
2. **Absolute URI Fragility**: Authoring cross-skill links with absolute workspace prefixes (`file:///.agents/skills/...` or drive letters `D:/...`) breaks portability across CI runners, Docker containers, remote execution sandboxes, and different developer checkout paths.

### Solution Pattern
1. **Pre-Parsing Codeblock Stripping**: Before evaluating structural AST rules (such as stage count detection, heading hierarchy, or link validity), linters must strip fenced code blocks (```` ```...``` ````) and inline backticks.
2. **Portable Relative Links**: Sibling cross-references within skill catalogs must strictly use standard relative paths (`../<sibling-skill>/SKILL.md`).
3. **Graceful Protocol Handling**: Linters should validate local relative paths against the filesystem while safely treating external URLs or illustrative protocols without crashing.

### Architectural Rules Enforced
- **Rule 20**: In-place deepening over shallow duplicate linters.
- **Rule 47**: Static markdown linter codeblock isolation and relative link invariant.
