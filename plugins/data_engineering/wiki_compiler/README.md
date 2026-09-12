# domain.wiki_compiler (v1.1.0)

Compiler-style dual in-memory / disk wiki builder with topological graph queries, incremental dirty-diff writing, and notes preservation

---

## Overview & Metadata

- **Plugin Directory**: `plugins/data_engineering/wiki_compiler`
- **Isolation Mode**: `subprocess`
- **Services Provided**: None
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `compile_wiki_directory` | `(raw_dir, output_dir, run_linter)` | Compile an entire raw notes directory into a cross-referenced Markdown wiki preserving notes |
| `compile_virtual_wiki` | `(notes, preserve_sections)` | Compile in-memory notes into a cross-referenced Markdown wiki without disk I/O |
| `query_wiki_graph` | `(raw_dir, notes, query_type, root_entity, target_entity, max_hops)` | Perform topological graph queries over the wiki mention network (neighborhood, backlinks, path, clusters) |
| `compile_wiki_incremental` | `(raw_dir, output_dir)` | Compile wiki pages only writing changed markdown files to disk (dirty-tracking diff writer) |
| `extract_entity_metadata` | `(file_path)` | Extract metadata, name, and aliases from a single note file |
| `build_reference_graph` | `(raw_dir)` | Extract all entities and compute the full directional cross-reference graph |
| `lint_wiki` | `(compiled_dir)` | Lint compiled wiki directory for broken [[wikilinks]] and unreferenced orphan pages |
| `generate_synthetic_notes` | `(output_dir, num_files, seed)` | Generate a synthetic corpus of raw notes with embedded cross-mentions for benchmarking |

---

## Key Modules & AST Symbols

### Module [`compiler_core.py`](compiler_core.py)

Core Wiki Compiler: Extraction, Phrase Index Mention Detection, Virtual Compilation, and Graph Analytics.

#### Classes

- `class Entity`
  - `def to_dict() -> dict[str, Any]`
- `class WikiGraphQuery`
  Graph analytics engine for topological querying over the wiki mention graph.
  - `def __init__(graph, entities)`
  - `def get_backlinks(entity_id) -> list[dict[str, str]]`
  - `def get_neighborhood(entity_id, max_hops) -> dict[str, Any]`
  - `def find_path(source_id, target_id) -> list[str] | None`
  - `def get_clusters() -> list[list[str]]`
- `class LintReport`
  - `def is_clean() -> bool`
  - `def to_dict() -> dict[str, Any]`


#### Functions

- `def extract_entity_from_text(text, identifier) -> Entity`
  - Extract entity structure from raw string text.
- `def extract_entity(path) -> Entity`
- `def extract_all(raw_dir) -> dict[str, Entity]`
- `def build_graph(entities) -> dict[str, dict[str, set[str]]]`
- `def orphan_ids(graph) -> list[str]`
- `def render_page(entity, graph_edges, entities, existing_content, existing_path) -> str`
- `def compile_virtual_wiki(notes, preserve_sections) -> dict[str, Any]`
  - Compile in-memory notes into a cross-referenced Markdown wiki without disk I/O.
- `def compile_pages(entities, graph, output_dir) -> list[str]`
- `def compile_pages_incremental(entities, graph, output_dir) -> dict[str, Any]`
  - Compile wiki pages only writing changed content (dirty-tracking diff writer).
- `def lint(output_dir) -> LintReport`
- `def generate_corpus(output_dir, num_files, seed) -> list[str]`
- `def compile_wiki(raw_dir, output_dir, run_lint) -> dict[str, Any]`


### Module [`main.py`](main.py)

Main entrypoint and typed tool registrations for Wiki Compiler plugin.

#### Classes

- `class WikiCompilerService`
  Service provider for Wiki Compilation and Knowledge Graph Navigation.
  - `def compile(raw_dir, output_dir, run_linter) -> dict[str, Any]`
  - `def compile_virtual(notes, preserve_sections) -> dict[str, Any]`
  - `def compile_incremental(raw_dir, output_dir) -> dict[str, Any]`
  - `def query_graph(raw_dir, notes, query_type, root_entity, target_entity, max_hops) -> dict[str, Any]`
  - `def extract(file_path) -> dict[str, Any]`
  - `def build_graph(raw_dir) -> dict[str, Any]`
  - `def lint(compiled_dir) -> dict[str, Any]`
  - `def generate_corpus(output_dir, num_files, seed) -> dict[str, Any]`


#### Functions

- `def compile_wiki_directory(raw_dir, output_dir, run_linter) -> dict[str, Any]`
  - Compile an entire raw notes directory into a cross-referenced Markdown wiki preserving notes.
- `def compile_virtual_wiki(notes, preserve_sections) -> dict[str, Any]`
  - Compile in-memory notes into a cross-referenced Markdown wiki without disk I/O.
- `def query_wiki_graph(raw_dir, notes, query_type, root_entity, target_entity, max_hops) -> dict[str, Any]`
  - Perform topological graph queries over the wiki mention network.
- `def compile_wiki_incremental(raw_dir, output_dir) -> dict[str, Any]`
  - Compile wiki pages only writing changed markdown files to disk (dirty-tracking diff writer).
- `def extract_entity_metadata(file_path) -> dict[str, Any]`
  - Extract metadata, name, and aliases from a single note file.
- `def build_reference_graph(raw_dir) -> dict[str, Any]`
  - Extract all entities and compute the full directional cross-reference graph.
- `def lint_wiki(compiled_dir) -> dict[str, Any]`
  - Lint compiled wiki directory for broken [[wikilinks]] and unreferenced orphan pages.
- `def generate_synthetic_notes(output_dir, num_files, seed) -> dict[str, Any]`
  - Generate a synthetic corpus of raw notes with embedded cross-mentions for benchmarking.



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
