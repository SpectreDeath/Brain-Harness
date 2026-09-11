---
name: multimedia-intelligence-forge
description: Ingest, transcribe, and distill multimedia lectures, technical videos, and literature into deep agent skills and cryptographically verified Knowledge Vault items. Do not use for generic audio/video editing or entertainment media consumption.
---

# Multimedia Intelligence Forge: Audio, Video & Knowledge Distillation

`multimedia-intelligence-forge` is an authoritative composite meta-skill that transforms unstructured multimedia assets—YouTube lectures, technical keynotes, conference recordings, and multimedia literature—into production-grade, architecturally deepened agent skills and cryptographically verified Knowledge Vault items.

It coordinates five specialized capabilities:
1. **Subprocess Transcript Ingestion** ([`youtube-transcript-fetcher`](../youtube-transcript-fetcher/SKILL.md))
2. **Dual-Lens Cognitive Distillation** ([`media-mind-forge`](../media-mind-forge/SKILL.md))
3. **End-to-End Deep Skill Synthesis** ([`deep-skill-forge`](../deep-skill-forge/SKILL.md))
4. **Cryptographic Isnad Verification** ([`epistemic-isnad-audit`](../epistemic-isnad-audit/SKILL.md))
5. **Epistemic Memory Promotion & Vault Retention** ([`epistemic-memory-lifecycle`](../epistemic-memory-lifecycle/SKILL.md))

See [CARD.md](CARD.md) for the companion summary card, 5-stage progression matrix, and invariants checklist.
Consult `/media-mind-forge` for dual-lens extraction heuristics, `/epistemic-isnad-audit` for cryptographic claim verification, and [multimodal-distillation.md](references/multimodal-distillation.md) for multimodal distillation heuristics.

---

## The 5-Stage Multimedia Distillation Progression

```
[1. Transcript Ingestion] ──► [2. Dual-Lens Distillation] ──► [3. Consolidated Master Checkpoint]
                                                                          │
                                                                          ▼
[5. Epistemic Vault Commit] ◄── [4. Deep Skill Scaffolding & Repair] ◄────┘
```

---

## 1. Multimedia Ingestion & Subprocess Transcription

Fetch and normalize spoken transcripts or written media via isolated subprocess pipes without shell injection vulnerabilities:

1. **Subprocess Audio/Transcript Acquisition (Rule 5 & Rule 15)**:
   - Extract full timed captions or transcripts via isolated JSON-RPC runners.
   - Prevent argument injection by passing sanitized video IDs/URLs directly to subprocess argv lists.
2. **Deterministic Pre-LLM Normalization (Rule 9)**:
   - Deduplicate filler phrases, vocal tics, and sponsor breaks.
   - Segment long-form transcripts into semantically coherent chapters anchored by timestamps.
3. **Primary Source Hashing**:
   - Compute the SHA-256 digest of the raw transcript text for immutable lineage tracking.

> **Completion criterion**: Clean, timestamp-segmented transcript generated with SHA-256 digest recorded.

---

## 2. Dual-Lens Cognitive Distillation

Apply the Dual-Lens Cognitive Distillation protocol (Rule 41), strictly bifurcating the raw material into two distinct output streams:

1. **Lens A: Epistemic Introspection (Ground-Truth Beliefs)**:
   - Extract core mental models, conceptual axioms, and philosophical heuristics.
   - Pin each claim directly to an exact timestamp or line quote (chain-of-custody lineage).
2. **Lens B: Procedural Skill Synthesis (Shu-Ha-Ri Execution)**:
   - Extract operational stages, binary completion criteria, diagnostic interview questions, and anti-patterns.
3. **Cognitive Salvage (Rule 42)**:
   - Cleanse extracted JSON schemas through multi-pass repair (strip fences, fix trailing commas, unquote keys).

> **Completion criterion**: Epistemic claims and procedural skill blueprints extracted and validated.

---

## 3. Visual Brief & Consolidated Checkpoint

Synthesize and present findings to the user before mutating persistent state:

1. **Interactive HTML Visual Brief**:
   - Render a dark-themed visual summary in `%TEMP%` showing transcript metrics, extracted mental models, and target skill architecture.
2. **Consolidated Master Checkpoint**:
   - Author `implementation_plan.md` with `RequestFeedback: true` detailing both proposed Knowledge Items and new agent skill files.
   - Await explicit user approval before proceeding to file creation.

> **Completion criterion**: Interactive HTML visual brief rendered and user sign-off obtained at master checkpoint.

---

## 4. Deep Skill Scaffolding & Bounded Self-Repair

Generate the complete production skill package following deep-module standards:

1. **Slotted & Frozen Dataclass Domain Models (Rule 12)**:
   - Author `@dataclass(slots=True, frozen=True)` schemas with `__post_init__` invariant guards.
2. **Craft Standards Specification**:
   - Generate `SKILL.md` (bounded description 100-350 chars with negative boundary, Rule 44).
   - Generate `CARD.md` with single-pipe ASCII borders and blocking checklist invariants (Rule 37).
   - Generate `config.default.yaml` for 3-tier zero-fork configuration.
3. **Bounded In-Flight Self-Repair**:
   - Execute contract tests in-flight; repair syntax or schema failures automatically up to 3 attempts.

> **Completion criterion**: Compliant skill package scaffolded with 100% passing tests within $\le 3$ repair attempts.

---

## 5. Epistemic Isnad Lineage & Knowledge Vault Commit

Commit ground-truth learnings to persistent memory according to repository invariants:

1. **Canonical Dual-File Directory Format (Rule 40)**:
   - Write `.harness/knowledge/<ki_id>/metadata.json` (SHA-256, source URI, claims, verification status).
   - Write `.harness/knowledge/<ki_id>/summary.md` (distilled narrative, mental models, decision heuristics).
2. **Ecosystem Context Map Registration**:
   - Register forged skills in `CONTEXT-MAP.md` under their appropriate domain.
3. **Skill Knowledge Graph Indexing**:
   - Index the new skill nodes and dependency edges into `skill_knowledge_graph`.

> **Completion criterion**: Canonical dual-file Knowledge Vault item committed, CONTEXT-MAP.md updated, and skill graph indexed.

---

## The Three Foundational Pillars

### 1. The Visual Brief Pillar
Every distillation run renders an interactive HTML visual brief in `%TEMP%` displaying speech timelines, isnad claim matrices, and synthesized skill component graphs.

### 2. The Mandatory Checkpoint Pillar
The agent must never author skill files or mutate persistent memory without first presenting `implementation_plan.md` with `RequestFeedback: true` and awaiting explicit user confirmation.

### 3. Explicit Anti-Patterns
Rigid architectural boundaries prevent ungrounded transcript hallucinations, flat vault pollution, and unbounded repair loops.

---

## Anti-Patterns

- **Ungrounded Transcript Hallucination** — Distilling claims or heuristics without verbatim quote evidence or timestamp references.
- **Single-File Vault Pollution** — Dumping single flat JSON files into `.harness/knowledge/` instead of the canonical dual-file directory (`metadata.json` + `summary.md`).
- **Collapsing Dual-Lens Seams** — Blending epistemic belief models and executable procedural skills into an undifferentiated prose blob.
- **Unbounded Repair Thrashing** — Retrying failing contract tests in an infinite loop without an explicit circuit breaker limit of 3 attempts.
- **Unverified Shell Redirection** — Piping transcript downloads through bare shell redirects instead of safe subprocess UTF-8 streams.
- **Missing Negative Deflection Boundary** — Scaffolding skills without explicit `Do not use for...` constraints in frontmatter descriptions.
