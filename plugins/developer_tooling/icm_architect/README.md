# ICM Architect Plugin

The `plugin.icm_architect` provides native Interpretable Context Methodology (ICM) architecture capabilities to Brain Harness.

Operating on the foundational research of Van Clief & McDermott (*Interpretable Context Methodology: Folder Structure as Agent Architecture*, arXiv:2603.16021), ICM replaces complex multi-agent framework code and prompt bloat with deterministic folder hierarchy, five-layer context scoping, and auditable stage checks.

## Architecture

```
[L0: AGENTS.md] ──► [L1: root CONTEXT.md] ──► [L2: stage CONTEXT.md]
                                                     │
                                       ┌─────────────┴─────────────┐
                                       ▼                           ▼
                             [L3: _shared/ factory]      [L4: output/ product]
```

## Tools Provided

1. **`icm_audit_workspace`**: Audits a workspace against the 10 mandatory invariants, classifies files into the 5-role taxonomy (`catalog`, `contract`, `factory`, `product`, `dead`), and evaluates per-step token load.
2. **`icm_verify_links`**: Walks and validates all relative links, contract inputs, and `@import` pointers, ensuring zero broken links across the workspace.
3. **`icm_verify_quotes`**: Verifies that quoted claims appear word-for-word in raw sources, flags dropped negations across cuts (`...`), and enforces keep-out phrase defenses.
4. **`icm_rebuild_index`**: Scans frontmatter metadata and first headings to generate deterministic `_index.md` files without manual editing drift.
5. **`icm_scaffold_form`**: Scaffolds clean, minimal workspaces adhering to one of the five canonical forms: `pipeline`, `record_library`, `knowledge_bundle`, `context_map`, or `system_map`.

## Service Resolution

```python
from harness.services.icm_architect import (
    ICM_ARCHITECT_SERVICE_KEY,
    resolve_icm_architect_service,
)

service = resolve_icm_architect_service(context)
audit_report = service.audit_workspace(".")
```
