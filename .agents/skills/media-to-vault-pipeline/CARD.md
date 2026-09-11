```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: media-to-vault-pipeline                                       │
│ SKILL: media-to-vault-pipeline                                        │
│ Category: multimedia / cognitive_distillation                        │
│ Version: 1.0.0                                                       │
│ Invocation: /media-to-vault-pipeline                                 │
│ Triggers: "media to vault pipeline", "youtube to skill",             │
│           "distill video", "commit video to vault",                  │
│           "transcribe and distill", "run media pipeline"             │
│ Requires: "youtube-transcript-fetcher",                              │
│           "multimedia-intelligence-forge", "media-mind-forge",       │
│           "epistemic-isnad-audit", "deep-skill-forge",               │
│           "agent-skill-sdlc"                                         │
│ Target: Dual-lens multimedia transcript distillation & vault commit  │
└──────────────────────────────────────────────────────────────────────┘
```

# Media to Vault Pipeline — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Transcript Ingestion** | Extract spoken dialogue and timestamped captions from video | Transcript JSON | Non-empty timed segments retrieved |
| **Stage 2: Dual-Lens Cognitive Distillation** | Bifurcate content into epistemic claims vs procedural steps | Distillation JSON | Dual-lens seam strictly partitioned (Rule 41) |
| **Stage 3: Isnad Provenance Verification** | Verify chain-of-custody against video timestamps | Isnad Ledger | Claims meet $\ge 0.85$ confidence threshold |
| **Stage 4: Mandatory Checkpoint Gate** | Present distilled findings and schema for confirmation | Implementation Plan | Explicit user confirmation received |
| **Stage 5: Vault Commit & Skill Scaffolding** | Persist canonical dual-file KI and scaffold agent skill | Knowledge Item & Skill | Canonical dual-file format validated (Rule 40) |

---

## Vocabulary & Levers

- **Dual-Lens Cognitive Distillation Seam**: Bifurcating raw media into epistemic ground-truth claims and procedural execution rubrics (Rule 41).
- **Isnad Provenance**: Unbroken chain-of-custody tracing each claim to a verified speaker timestamp or external citation.
- **Canonical Dual-File Directory Format**: Storing Knowledge Vault items strictly as `<ki_id>/metadata.json` + `summary.md` (Rule 40).
- **Zero-Fork Operational Config**: Defining baseline runtime budgets in `config.default.yaml` for three-tier configuration (Rule 44).
- **Slotted/Frozen Data Structures**: Utilizing `slots=True, frozen=True` across internal entities (Rule 12).

---

## Mandatory Invariants Checklist

- [ ] **Dual-Lens Seam Bifurcation**: Strictly partition media extraction into epistemic claims and procedural actions (Rule 41).
- [ ] **Canonical Dual-File Directory Format**: Knowledge items must persist as `metadata.json` + `summary.md` under `.harness/knowledge/<ki_id>/` (Rule 40).
- [ ] **Cryptographic Isnad Provenance**: Every extracted claim must reference a timestamped segment or verifiable isnad link.
- [ ] **Deterministic File-Based JSON Output**: All CLI inspection subcommands must write structured JSON to `--output` (Rule 4).
- [ ] **Zero-Fork Operational Config**: Operational budgets must resolve from `config.default.yaml` without repo forks (Rule 44).
