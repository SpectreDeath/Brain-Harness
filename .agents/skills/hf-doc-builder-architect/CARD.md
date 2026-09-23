```ascii
┌─────────────────────────────────────────────────────────────────────────────┐
│ SKILL: hf-doc-builder-architect                                             │
│ Category: developer_tooling / documentation                                 │
│ Version: 1.0.0                                                              │
│ Invocation: /hf-doc-builder-architect                                       │
│ Triggers: "hf doc builder architect", "autodoc inspection", "doc builder",  │
│           "check doc links", "mdx transpilation", "doc chunking"            │
│ Requires: "developer-docs-architect", "repo-doc-synchronizer"               │
│ Target: Multi-package doc compilation, mock virtualization & MDX chunking   │
└─────────────────────────────────────────────────────────────────────────────┘
```

# HF Doc Builder Architect — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: AST Extraction** | Extract signatures, parameter specs & type hints | `AutodocSignature` | Structured signature generated with parameter list |
| **Stage 2: Mock Virtualization** | Intercept imports via `sys.meta_path` hooks | `MockFinder` | Target Python package imports without dependencies |
| **Stage 3: MDX Transpilation** | Transpile Markdown, RST, IPYNB into Svelte MDX | Converted `.mdx` | Unified MDX generated with reactive Svelte tags |
| **Stage 4: Anchor Verification** | Resolve relative links and heading anchors | `LinkValidationReport` | 0 broken relative links and 0 dead anchors |
| **Stage 5: Search Chunking** | Heading-bounded chunking with breadcrumbs | `tuple[DocChunk, ...]` | Structured chunk nodes with breadcrumb lineage |

---

## Vocabulary & Levers

- **Zero-Dependency Mock Virtualization**: Deploying `MockFinder` on `sys.meta_path` to synthesize `_MockModule` and `_MockBaseMeta` proxies, avoiding heavy CUDA installations.
- **Deterministic Anchor Graph**: Parsing heading slugs and HTML IDs while masking code fences to verify link integrity without network requests.
- **Heading-Bounded Semantic Chunking**: Partitioning documentation trees along `H1` -> `H2` -> `H3` boundaries rather than arbitrary token counts.
- **Svelte MDX Callouts**: Transpiling blockquotes and Sphinx directives into reactive `<Tip>`, `<Warning>`, `<FrameworkContent>`, and `<InferenceSnippet>` tags.

---

## Mandatory Invariants Checklist

- [ ] **Slotted & Frozen Dataclasses**: All domain models must declare `slots=True, frozen=True` (Rule 12, Rule 43).
- [ ] **Subprocess Sandbox Isolation**: External documentation builds must execute in isolated subprocess sandboxes (Rule 5).
- [ ] **Subprocess Pipe Drainage**: All subprocess transports must drain and close pipes in `finally` blocks (Rule 14).
- [ ] **Canonical Dual-File Vault**: Persisted knowledge items must strictly use `metadata.json` + `summary.md` (Rule 40).
- [ ] **Bounded Self-Repair Circuit Breaker**: Test failure self-repairs must halt at $\le 3$ attempts before escalating.
