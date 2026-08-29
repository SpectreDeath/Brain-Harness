# Skill Summary Card — `cellcog-multimodal`

```
================================================================================
SKILL SUMMARY CARD: cellcog-multimodal
================================================================================
Category:     integration_and_io / multimodal
Invocation:   /cellcog-multimodal
Triggers:     "3d model", "generate video", "podcast", "excel spreadsheet",
              "presentation slides", "deep research", "cellcog"
Target:       Cross-modality generative asset & document synthesis
Plugin:       plugins/integration_and_io/cellcog/ (plugin.cellcog)
Service Key:  CELLCOG_SERVICE_KEY (service.cellcog)
================================================================================
```

---

## Stage Progression Table

| Stage | Name | Key Activity | Completion Gate |
|---|---|---|---|
| **1** | **Task Assessment** | Select `chat_mode` (`agent`/`creative`/`team`) and `chat_tier` (`flash`/`core`/`max`) | Target modality and tier documented |
| **2** | **Tag Protocol** | Embed `<SHOW_FILE>` inputs and `<GENERATE_FILE>` output destinations | Prompt sanitized and validated |
| **3** | **Visual Brief** | Generate HTML graph in `%TEMP%\cellcog-delegation-<timestamp>.html` | Visual brief written and linked |
| **4** | **Mandatory Checkpoint** | Present `implementation_plan.md` (`RequestFeedback: true`) | Explicit user sign-off |
| **5** | **Execution & Verification** | Invoke `cellcog_run` / `cellcog_research`, verify on-disk artifacts | Deliverables validated on filesystem |

---

## Vocabulary & Levers Cheat Sheet

- **Any-to-Any**: Single-request transformation from arbitrary input types (PDF, CSV, audio, images) to multiple multimodal deliverables.
- **`<SHOW_FILE>`**: Tag wrapping absolute local paths for multimodal upload and structural inspection by the sub-agent.
- **`<GENERATE_FILE>`**: Tag specifying the exact local destination path for output deliverables.
- **`chat_mode`**: Operating persona selector: `agent` (heavy pipelines/assets), `creative` (UI/design/writing), `team` (deep multi-source research).
- **`chat_tier`**: Compute/spend tier: `flash` (fast/economical), `core` (balanced), `max` (production depth).

---

## Invariants & Guardrails

1. **Security Guardrail**: Never enclose credentials, `.env`, `.git`, or private keys in `<SHOW_FILE>` tags.
2. **Deterministic Output**: Always provide `<GENERATE_FILE>` tags for expected binary deliverables (PDF, GLB, MP4, XLSX).
3. **Team Mode Constraint**: Reserve `chat_mode="team"` strictly for deep multi-source research tasks; use `agent` max for asset generation.
4. **Mandatory Gate**: Never execute unapproved cloud sub-agent tasks without the Stage 4 checkpoint.

---

## Disclosed Reference

- Consult [REFERENCE.md](REFERENCE.md) for golden prompt recipes covering 3D assets, 4K video, dashboards, spreadsheets, and deep research.
