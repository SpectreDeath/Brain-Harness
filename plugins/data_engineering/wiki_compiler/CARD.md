# 🧠 Skill Summary Card: `wiki_compiler`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        wiki_compiler                             │
│ Category:    data_engineering                          │
│ Archetype:   tool_provider / service_provider          │
│ Isolation:   subprocess                                │
│ Status:      Verified & Sandboxed                      │
├────────────────────────────────────────────────────────┤
│ Target:      Deterministic Pure-Python Wiki Compiler   │
└────────────────────────────────────────────────────────┘
```

## Tools
- `compile_wiki_directory(raw_dir, output_dir, run_lint=True)`: Compiles notes to cross-linked wiki pages.
- `extract_entity_metadata(file_path)`: Regex extraction of name, aliases, dates.
- `build_reference_graph(raw_dir)`: Bidirectional mention graph with phrase indexing.
- `lint_wiki(output_dir)`: Validates broken `[[links]]` and orphan pages.
- `generate_synthetic_notes(output_dir, num_files=50, seed=42)`: Test corpus generator.
