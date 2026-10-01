# Hugging Face Doc Builder Plugin (`plugin.hf_doc_builder`)

The `plugin.hf_doc_builder` plugin provides deep integration with Hugging Face doc-builder patterns for AST autodoc inspection, deterministic link verification, table-of-contents (`_toctree.yml`) auditing, MDX transpilation, and semantic markdown chunking.

---

## Central Function & Capabilities

1. **AST Autodoc Extraction (`doc_autodoc_inspect`)**: Inspects Python classes and functions using AST traversal to extract signatures, type hints, parameter docs, and return descriptions without executing untrusted module-level code.
2. **Deterministic Link & Anchor Verification (`doc_link_verify`)**: Scans Markdown and MDX documents, strips code blocks, and validates relative file paths, internal section anchors (`#heading`), and cross-references.
3. **Table of Contents Integrity Auditing**: Verifies that every entry in `_toctree.yml` resolves to a real documentation page and flags any orphaned documentation files.
4. **Format Transpilation (`doc_format_convert`)**: Transpiles standard Markdown, RST, and Jupyter Notebooks into MDX with Svelte tags.
5. **Semantic Document Chunking (`doc_markdown_chunk`)**: Chunks documentation at heading boundaries into token-bounded slices for retrieval-augmented generation.

---

## Architectural Invariants

- **Subprocess Pipe Disposal (Rule 14)**: The `HfDocBuilderSubprocessService` executes command-line operations with strict `finally` blocks explicitly closing `stdin`, `stdout`, and `stderr` pipes.
- **Plugin Module Singleton (Rule 45)**: Entrypoint `main.py` subclasses `HarnessPlugin`, implements `HfDocBuilderProtocol`, provides `DOC_BUILDER_SERVICE_KEY` in `on_load`, and exports `plugin = HfDocBuilderPlugin()`.
- **Codeblock Isolation (Rule 47)**: Strips code fences (```` ```...``` ````) prior to link parsing, preventing false positives on type annotations or shell commands.
- **Micro-Kernel Seam Elevation (Rule 49)**: Core logic is implemented in the slotted domain engine `DocBuilderDomainEngine` (`src/harness/services/doc_builder.py`) and resolved in-memory via `context.require(DOC_BUILDER_SERVICE_KEY)`.

---

## Key Modules & Classes

| Module | Core Classes | Description |
|---|---|---|
| [`main.py`](main.py) | `HfDocBuilderPlugin`, `plugin` | Subclasses `HarnessPlugin`, declares service keys, and registers tools into `ToolRegistry`. |
| [`service.py`](service.py) | `HfDocBuilderSubprocessService` | Adapts `DocBuilderDomainEngine` with subprocess pipe protection and resource bounding. |
| [`plugin.json`](plugin.json) | — | Declares plugin metadata, permissions, tools, and `service.doc_builder` provision. |

---

## Exposed Agent Tools

| Tool Name | Parameters | Description |
|---|---|---|
| `doc_autodoc_inspect` | `package_name`, `object_name`, `mock_heavy_deps` | Extracts structured autodoc signature data from Python objects. |
| `doc_link_verify` | `docs_dir`, `check_anchors`, `check_toc` | Validates relative file links, anchors, and TOC integrity. |
| `doc_format_convert` | `source_path`, `target_format` | Transpiles Markdown/RST to MDX with Svelte syntax. |
| `doc_style_lint` | `file_path`, `fix` | Audits style compliance and heading structure. |
| `doc_markdown_chunk` | `markdown_text`, `page_title`, `max_chunk_size` | Chunks markdown into heading-bounded semantic segments. |

---

## Programmatic Usage Example

```python
import asyncio
from pathlib import Path
from harness.kernel.runtime import HarnessRuntime
from harness.services.doc_builder import DOC_BUILDER_SERVICE_KEY

async def verify_documentation_suite():
    async with HarnessRuntime.create() as runtime:
        doc_service = runtime.context.require(DOC_BUILDER_SERVICE_KEY)
        
        # Verify relative links and TOC integrity
        report = doc_service.verify_links(
            docs_dir=Path("docs"),
            check_anchors=True,
            check_toc=True,
        )
        
        print(f"Scanned files: {report.scanned_files_count}")
        print(f"Total links: {report.total_links_checked}")
        print(f"Valid: {report.valid}")
        print(f"Broken links: {len(report.broken_links)}")
        print(f"Orphaned docs: {len(report.orphaned_files)}")

if __name__ == "__main__":
    asyncio.run(verify_documentation_suite())
```

---

## Related Documentation

- [HF Doc Builder Skill Reference](../../../.agents/skills/hf-doc-builder-architect/SKILL.md)
- [Doc Builder Service Protocol](../../../src/harness/services/doc_builder.py)
- [Documentation Suite Hub](../../../docs/README.md)
