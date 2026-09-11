# Epistemic Isnad Lineage & Knowledge Distillation

## What is Isnad Lineage?

In the Brain Harness architecture, an **isnad** (Arabic: إسناد, "chain of custody / support") is an unbroken provenance record connecting synthesized knowledge and architectural assertions directly to primary source artifacts.

Every architectural decision and mental model committed to persistent memory must trace back to:
1. **Primary Literature Source**: Author, publication, URL, or commit hash.
2. **Cryptographic Integrity**: SHA-256 digest of the ingested source material.
3. **Verifiable Claims List**: Atomic assertions paired with direct evidence quotes.

---

## Canonical Knowledge Vault Dual-File Format (Rule 40)

To prevent indexer crashes and maintain human-and-agent readability, all knowledge items under `.harness/knowledge/<ki_id>/` must strictly adhere to the dual-file directory format:

### 1. `metadata.json`
```json
{
  "id": "ki_codebase_context_management",
  "title": "Three-Layer Codebase Context Management",
  "source_uri": "https://www.freecodecamp.org/news/how-to-manage-context-files-in-your-codebase-and-get-better-agent-output/",
  "sha256": "8a3f...",
  "created_at": "2026-09-07T19:00:00Z",
  "category": "agent-architecture",
  "claims": [
    {
      "claim_id": "claim_001",
      "assertion": "Instruction retrieval degrades as token count climbs due to context rot.",
      "evidence_quote": "Anthropic's engineering team describes an effect they call context rot..."
    }
  ]
}
```

### 2. `summary.md`
Markdown document detailing:
- Executive Summary
- Ground-Truth Mental Models
- Architectural Decision Heuristics
- Anti-Pattern Defenses and Invariant Rules
