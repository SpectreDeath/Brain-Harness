# Deterministic Markdown Anchor Graph & Cross-Reference Link Verification

## Context
Extracted from Hugging Face `doc-builder`'s 80KB link checking engine (`src/doc_builder/check_links.py`, commit `bcd143e`). In multi-version documentation systems with hundreds of interdependent packages, link rot (dead anchors, broken relative paths, missing cross-package references) causes broken developer experiences.

## Distilled Mental Model & Engineering Breakthrough
The engine decomposes link verification into high-speed lexical and structural passes:
1. **Fenced & Inline Code Shielding**: Isolates code fences (```) and inline backticks (`...`) prior to link extraction using range masks to eliminate false-positive link matches on code syntax.
2. **Anchor Index Construction**: Traverses markdown headers (`#`, `##`), HTML tags (`<a id="...">`, `<div id="...">`), and custom autodoc blocks (`[[autodoc]]`) to construct an in-memory `_AnchorIndex`.
3. **Extensionless Route Resolution**: Resolves links written without explicit `.md` or `.mdx` extensions (e.g., `./quickstart` resolving against `quickstart.md` or `quickstart.mdx` or `quickstart/index.md`).
4. **Anchor Normalization**: Slugifies headings using GitHub/GitLab compatible anchor rules, verifying exact fragment identifiers (`#my-anchor`).

## Triggers & Seam Choices
- **Trigger**: Pre-commit hooks, CI documentation verification, and documentation refactoring pipelines.
- **Seam Choice**: Integrate via `HfDocBuilderService.verify_links()` or CLI `harness docs check-links`.
