---
name: hf-doc-builder-architect
description: Architect, compile, and verify multi-package documentation using zero-dependency mock virtualization, deterministic AST anchor graphs, and unified MDX transpilation. Do not use for generic prose editing or static site hosting.
---

# HF Doc Builder Architect: Multi-Package Documentation Engineering

`hf-doc-builder-architect` is the authoritative documentation compilation and verification engine for Brain Harness, distilled from Hugging Face `doc-builder` (`hf-doc-builder`). It provides zero-dependency mock virtualization for Python AST introspection, deterministic Markdown anchor graph verification, multi-dialect MDX transpilation, and heading-bounded semantic chunking.

See [CARD.md](CARD.md) for the companion summary card, 5-stage progression matrix, and invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline operational budgets and zero-fork configuration.
Refer to [developer-docs-architect](../developer-docs-architect/SKILL.md) for Diataxis documentation taxonomy.

---

## The 5-Stage Shu-Ha-Ri Operational Pipeline

```
[1. Docstring & AST Extraction] ──► [2. Zero-Dep Mock Virtualization] ──► [3. Multi-Dialect MDX Compilation]
                                                                                       │
                                                                                       ▼
[5. Hierarchical Chunk & Vector Index] ◄── [4. Anchor Graph & TOC Verification] ◄──────┘
```

---

## 1. Stage 1 (Shu): Docstring & AST Extraction

Extract structured signatures, type annotations, and docstrings from Python modules:

1. **Object Resolution**:
   - Locate target objects (classes, methods, functions) in the specified package hierarchy.
   - Detect docstring syntax: Google style, NumPy style, or reStructuredText (Sphinx).
2. **Signature Normalization**:
   - Parse `inspect.signature` or AST argument nodes, preserving default values and type annotations.
   - Separate positional-only, keyword-only, `*args`, and `**kwargs`.
3. **Structured Parameter Table**:
   - Map parameters to typed definitions with extracted doc descriptions.

> **Completion criterion**: Structured `AutodocSignature` generated with valid parameter list and return type.

---

## 2. Stage 2 (Shu): Zero-Dependency Mock Virtualization

Introspect deep learning and native modules without hardware or dependency overhead:

1. **Meta-Path Import Interception**:
   - Deploy `MockFinder` into `sys.meta_path` to intercept uninstalled third-party modules (e.g., `torch`, `tensorflow`, `jax`, `flax`).
2. **Metaclass Inheritance Shielding**:
   - When documented classes subclass external types (`class Model(nn.Module)`), dynamically synthesize proxy base classes so module loading never raises `TypeError`.
3. **Distribution & Version Spoofing**:
   - Intercept `importlib.metadata.version` calls to return mock SemVer versions satisfying runtime version gates.

> **Completion criterion**: Target Python package imports successfully and inspects cleanly in an unprovisioned environment.

---

## 3. Stage 3 (Ha): Multi-Dialect MDX Compilation

Transpile disparate documentation dialects into unified, reactive Svelte MDX:

1. **Dialect Normalization**:
   - Convert standard Markdown, reStructuredText (Sphinx directives), and Jupyter Notebooks (`.ipynb`) into unified MDX.
2. **Component Tag Injection**:
   - Translate doc callouts into reactive component tags (`<Tip>`, `<Warning>`, `<FrameworkContent>`, `<InferenceSnippet>`).
3. **Codeblock Formatting**:
   - Lint and format Python example blocks using Ruff, stripping internal test harnesses or doctest artifacts.

> **Completion criterion**: Unified `.mdx` output generated with valid component tags and formatted examples.

---

## 4. Stage 4 (Ha): Anchor Graph & TOC Verification

Ensure 100% link integrity and navigation tree completeness:

1. **Code & Comment Masking**:
   - Strip code fences (```) and inline backticks to prevent false-positive link matches.
2. **Anchor Index Construction**:
   - Extract heading slugs (`#heading-title`), HTML IDs (`<a id="...">`), and autodoc anchors into an in-memory graph.
3. **Extensionless Route Resolution**:
   - Resolve relative links written without extensions (`./pipeline` -> `./pipeline.md` or `./pipeline.mdx`).
4. **Table of Contents Integrity**:
   - Audit `_toctree.yml` against filesystem to detect dead links and orphaned pages.

> **Completion criterion**: 0 broken relative links, 0 dead anchors, and complete TOC coverage.

---

## 5. Stage 5 (Ri): Hierarchical Chunking & Semantic Search

Partition documentation for hybrid vector and full-text retrieval:

1. **Heading Tree Partitioning**:
   - Split documentation along `H1` -> `H2` -> `H3` boundaries rather than arbitrary token counts.
2. **Breadcrumb Hierarchy Preservation**:
   - Attach the full navigation path (`Library > Guide > Section`) to each chunk payload.
3. **Dense & Sparse Index Payload**:
   - Emit structured chunks with character and token bounds, ready for Meilisearch full-text or embedding ingestion.

> **Completion criterion**: Structured array of `DocChunk` nodes emitted with hierarchical breadcrumbs and token estimates.

---

## The Three Foundational Pillars

### 1. Zero-Dependency Mock Virtualization
Never fail AST documentation introspection due to missing CUDA or heavy frameworks. Use in-process meta-path interception to virtualize dependencies dynamically.

### 2. Deterministic Anchor Graph Integrity
Never ship broken relative links or dead heading anchors. Lexically mask codeblocks and verify the complete anchor graph across files and extensionless routes.

### 3. Unified Transpilation & Semantic Boundaries
Never treat technical docs as flat text. Transpile multi-dialect sources into structured MDX and chunk along structural heading trees for precise LLM retrieval.

---

## Slotted & Frozen Dataclass Domain Architecture

All domain models use `slots=True` and `frozen=True` (Rule 12):
- `AutodocParameter(slots=True, frozen=True)`
- `AutodocSignature(slots=True, frozen=True)`
- `LinkDiagnostic(slots=True, frozen=True)`
- `LinkValidationReport(slots=True, frozen=True)`
- `DocChunk(slots=True, frozen=True)`

---

## Anti-Patterns

- **Environment-Coupled Inspection** — Requiring full CUDA / GPU machine learning environments to extract docstrings instead of utilizing PEP 302/451 meta-path mock virtualization.
- **Unshielded Codeblock Link Crawling** — Running regex link matchers over unparsed Markdown without stripping code fences, producing false-positive link errors on Python code syntax.
- **Arbitrary Token Slicing** — Chopping technical documentation into fixed 512-token chunks that split method signatures from parameter descriptions instead of bounding along heading trees.
- **Orphan Page Accumulation** — Publishing documentation pages that are omitted from `_toctree.yml` navigation manifests, creating unindexed dark documentation.
- **Unbounded Relative Route Failure** — Failing on extensionless links (`./quickstart`) instead of attempting multi-extension resolution (`.md`, `.mdx`, `/index.md`).
