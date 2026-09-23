# Multi-Dialect Unified MDX Transpilation & Hierarchical Search Chunking

## Context
Extracted from Hugging Face `doc-builder`'s compilation and embedding pipelines (`convert_md_to_mdx.py`, `convert_rst_to_mdx.py`, `build_embeddings.py`). Technical documentation arrives in disparate formats (RST from Sphinx legacy, Markdown from READMEs, IPYNB from Colab tutorials) requiring unified presentation and semantic searchability.

## Distilled Mental Model & Engineering Breakthrough
The pipeline unifies documentation ingestion and retrieval:
1. **Dialect Normalization**: Translates Sphinx `:class:` and `:func:` directives, raw HTML tags, and Jupyter cell metadata into clean MDX with custom interactive tags (`<Tip>`, `<Warning>`, `<FrameworkContent>`, `<InferenceSnippet>`).
2. **Heading-Bounded AST Chunking**: Rather than arbitrary character or token sliding windows, documents are partitioned along structural heading trees (`H1` -> `H2` -> `H3`). Each chunk preserves the breadcrumb path (`PageTitle > Section > Subsection`), retaining hierarchical context for LLM retrieval.
3. **Dense + Sparse Hybrid Indexing**: Generates text excerpts, embedding vectors, and Meilisearch document payloads with vectorless full-text fallback (commits `953aa44`, `c2d27f6`).

## Triggers & Seam Choices
- **Trigger**: Knowledge base ingestion, documentation publishing, and RAG index population.
- **Seam Choice**: Integrate via `HfDocBuilderService.convert_format()` and `HfDocBuilderService.chunk_document()`.
