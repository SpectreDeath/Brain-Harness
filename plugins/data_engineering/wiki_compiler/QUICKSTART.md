# Wiki Compiler Plugin — Quickstart Guide

The `domain.wiki_compiler` plugin turns messy, unstructured text notes into a linked, linted Markdown wiki without any LLM calls or external dependencies.

## 🔄 Four-Stage Compiler Pipeline
1. **Extractor**: Regex scan extracting entity name, aliases, creation date, and body text.
2. **Graph**: Word-indexed phrase matcher detecting cross-entity mentions and building bidirectional links.
3. **Rewriter**: Compiles `## Metadata`, `## Related`, `## Referenced By`, and `## Body`, while preserving human-written `## Notes`.
4. **Linter**: Verifies zero broken `[[links]]` and surfaces orphan pages.

## 🚀 Quick Usage

```python
from plugins.data_engineering.wiki_compiler.main import (
    generate_synthetic_notes, compile_wiki_directory, lint_wiki
)

# 1. Generate synthetic notes corpus
generate_synthetic_notes("raw_notes", num_files=20, seed=42)

# 2. Compile into clean markdown wiki
result = compile_wiki_directory("raw_notes", "compiled_wiki")
print(f"Compiled {result['pages_compiled']} pages with {result['edges_count']} cross links.")

# 3. Lint the wiki
lint_res = lint_wiki("compiled_wiki")
print(f"Broken links: {len(lint_res['report']['broken_links'])}, Orphans: {len(lint_res['report']['orphan_pages'])}")
```
