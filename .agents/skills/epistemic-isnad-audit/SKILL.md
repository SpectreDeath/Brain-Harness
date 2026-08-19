---
name: epistemic-isnad-audit
description: Verify unbroken chain-of-custody lineage for facts, dependencies, and architectural decisions before writing to persistent state or memory. Use when the user asks for an epistemic audit, to verify claim lineage, to check isnad traceability, or before committing architectural decisions to persistent stores.
---

# Epistemic Isnad Audit Engine

The `epistemic-isnad-audit` engine operationalizes the classical Islamic *Isnad* (chain of custody) methodology combined with Neo-Confucian *Empty Mind* extraction. It mandates cryptographic-grade traceability for all factual assertions, ensuring no hallucinated, unanchored, or speculative claims enter long-term architectural records (`.context/decisions.md`, memory engines, or kernel manifests).

Every isnad audit follows a strict five-stage progression:

```
[1. Pure Extraction (Empty Mind)] → [2. Isnad Lineage Tracing] → [3. Visual Lineage Brief (Temp HTML)] → [4. Verification Checkpoint] → [5. Structured Isnad Commit]
```

See [CARD.md](CARD.md) for the quick-reference summary card, lineage schemas, and completion criteria.
Consult `/crafting-skills` for the underlying design standard and three foundational pillars.

---

## 1. Pure Extraction (Zhu Xi Empty Mind)

Isolate and extract factual assertions from raw context without adding evaluative judgments, speculative inferences, or confirmation bias:

1. **Raw Claim Segmentation**: Deconstruct candidate proposals into atomic factual propositions (e.g., "Module X imports Module Y", "Service key Z requires generic type T").
2. **Suspension of Evaluation**: Record each statement in its raw descriptive state prior to synthesis or critique.
3. **Extraction Table**: Produce an unannotated claim inventory.

> **Completion criterion**: Discrete list of atomic claims extracted with zero interpretive commentary.

---

## 2. Isnad Lineage Tracing (Chain of Custody Resolution)

Map every extracted claim to an unbroken chain of custody terminating at a primary workspace node:

1. **Lineage Node Types**:
   - **Primary Code Source**: Exact file path and line slice (`[service.py:L40-L65](file:///d:/path/to/service.py#L40-L65)`).
   - **Tool Execution**: Deterministic command / tool result (`run_command` output, `pytest` exit code).
   - **Declarative Manifest**: Grounded schema file (`pyproject.toml`, `plugin.json`).
2. **Lineage Audit Table**:
   ```markdown
   | Claim ID | Proposition | Primary Source / Tool Event | Lineage Status |
   | :--- | :--- | :--- | :--- |
   | `C-101` | ServiceKey requires generic parameter | `src/harness/kernel/service.py#L12-L30` | `VERIFIED` |
   | `C-102` | Subprocess isolation is enabled by default | `src/harness/plugins/loader.py#L88-L104` | `VERIFIED` |
   | `C-103` | Memory engine auto-indexes on startup | `None (Inferred)` | `HYPOTHESIS [UNVERIFIED]` |
   ```
3. **Ungrounded Claim Isolation**: Any claim without a direct primary node is strictly labeled `HYPOTHESIS [UNVERIFIED]`.

> **Completion criterion**: 100% of claims classified as either `VERIFIED` with file URIs or `HYPOTHESIS [UNVERIFIED]`.

---

## 3. The Visual Lineage Brief

Synthesize the audited claims and their provenance trees into an interactive HTML report:

1. **Target Path**: Write to `%TEMP%\isnad-audit-<timestamp>.html` (Windows) or `/tmp/isnad-audit-<timestamp>.html` (Unix).
2. **Visual Standards**:
   - Load Tailwind CSS and Mermaid.js via CDN in a sleek dark theme (`#0d1117`).
   - Render a Mermaid **Lineage DAG** mapping assertions back to file sources and test receipts.
   - Highlight unverified hypotheses in warning yellow (`#d29922`) and verified nodes in green (`#238636`).
3. **Surface**: Deliver the absolute, clickable HTML file path to the user.

```html
<!-- Location: %TEMP%\isnad-audit-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Isnad Epistemic Audit Brief</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto font-sans">
  <header class="border-b border-[#30363d] pb-4 mb-6">
    <h1 class="text-2xl font-bold text-white">Epistemic Isnad Chain of Custody</h1>
    <p class="text-sm text-gray-400 mt-1">Provable Provenance & Factual Lineage Graph</p>
  </header>
  <!-- Interactive Lineage DAG and Audit Matrix -->
</body>
</html>
```

> **Completion criterion**: Self-contained HTML report written to `%TEMP%` and delivered to user.

---

## 4. Verification Checkpoint (Grounding Resolution)

Resolve unverified hypotheses before allowing state mutation:

1. For each `HYPOTHESIS [UNVERIFIED]`, execute targeted inspection tools (`view_file`, `grep_search`, `run_command`).
2. If confirmed, promote to `VERIFIED` with exact file/line links.
3. If ungrounded or contradicted, discard the claim from the decision set.
4. Set `RequestFeedback: true` in the `implementation_plan.md` artifact and pause for user review.

> **Completion criterion**: Zero unverified hypotheses remaining in the active plan; user approval received.

---

## 5. Structured Isnad Commit

Emit the verified decision record with its complete provenance block to `.context/decisions.md` or persistent memory:

```markdown
## Decision: [Decision Title]

- **Timestamp**: YYYY-MM-DDTHH:MM:SSZ
- **Status**: ACCEPTED
- **Summary**: Concise description of verified architectural decision.

### Isnad Lineage Block
```json
{
  "decision_id": "dec_20260819_01",
  "claims": [
    {
      "assertion": "Service registration requires generic ServiceKey[T]",
      "lineage": [
        {"node": "primary_code", "uri": "file:///src/harness/kernel/service.py#L42-L68"},
        {"node": "verification_test", "uri": "file:///tests/kernel/test_service.py#L15-L35"}
      ]
    }
  ]
}
```
```

> **Completion criterion**: Structured Isnad record written to persistent store with 100% verified links.

---

## Anti-Patterns

- **Floating Assertions** — Stating facts or architectural guarantees without citing concrete source lines or tool outputs.
- **Inference Conflation** — Treating logical inferences or plausible assumptions as established ground truth.
- **Stale Lineage Pointers** — Citing out-of-date line ranges without verifying against the current workspace state.
- **Unanchored Memory Commits** — Writing unverified decisions into persistent memory or documentation.
