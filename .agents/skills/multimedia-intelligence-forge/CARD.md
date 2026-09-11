```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: multimedia-intelligence-forge                                 │
│ SKILL: multimedia-intelligence-forge                                  │
│ Category: integration_and_io / meta-skills                           │
│ Version: 1.0.0                                                       │
│ Invocation: /multimedia-intelligence-forge                           │
│ Triggers: "multimedia intelligence forge", "distill lecture",        │
│           "video to skill", "multimodal distillation", "forge media" │
│ Requires: "youtube-transcript-fetcher", "media-mind-forge",          │
│           "deep-skill-forge", "epistemic-isnad-audit",               │
│           "epistemic-memory-lifecycle"                               │
│ Target: End-to-end multimedia transcription, skill & KI distillation │
└──────────────────────────────────────────────────────────────────────┘
```

# Multimedia Intelligence Forge — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Ingest & Transcribe** | Fetch transcript via subprocess & compute SHA | Normalized Transcript | SHA-256 computed & timestamps segmented |
| **Stage 2: Dual-Lens Distillation** | Bifurcate into epistemic claims & procedures | 2-Stream Blueprint | Isnad claims & Shu-Ha-Ri stages isolated |
| **Stage 3: Master Checkpoint** | Render visual brief & present master plan | Visual Brief & Plan | HTML brief in `%TEMP%` & user approval |
| **Stage 4: Scaffold & Repair** | Scaffolding skill package & bounded repair | Tested Skill Package | 100% tests pass within $\le 3$ repair attempts |
| **Stage 5: Vault Retention** | Author dual-file KI & index skill graph | Dual-File KI & Graph | Canonical dual-file committed & graph updated |

---

## Vocabulary & Levers

- **Dual-Lens Cognitive Distillation**: Bifurcating media into ground-truth epistemic beliefs and actionable procedural skills (Rule 41).
- **Isnad Chain-of-Custody**: Cryptographic lineage tracing every claim to a primary source quote, timestamp, and SHA-256 hash.
- **Cognitive Multi-Pass Salvage**: Automated AST and string clean-up repairing malformed JSON before model reprompting (Rule 42).
- **Bounded In-Flight Self-Repair**: Bounded 3-attempt circuit-breaker loop resolving syntax and test errors without user interruption.
- **Canonical Knowledge Vault Dual-File**: Writing `metadata.json` + `summary.md` under `.harness/knowledge/<ki_id>/` (Rule 40).
- **Subprocess Isolation**: Fetching external multimedia transcripts via isolated runner processes without shell injection (Rule 15).

---

## Mandatory Invariants Checklist

- [ ] **Dual-Lens Seam Bifurcation**: Always separate epistemic claims from procedural skill execution (Rule 41).
- [ ] **Cryptographic Isnad Hashing**: Record SHA-256 digest of raw transcripts before extracting assertions.
- [ ] **Consolidated Approval Gate**: Never write code or create skill files without explicit user confirmation at Stage 3.
- [ ] **Bounded In-Flight Self-Repair**: Automated test repairs must strictly halt at a maximum of 3 attempts before escalating.
- [ ] **Canonical Dual-File Vault Format**: Knowledge items must be written as directory with `metadata.json` and `summary.md` (Rule 40).
