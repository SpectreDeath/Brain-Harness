# Example: Deck Builder Skill — Full v1 to v5 Evolutionary Walkthrough

This case study illustrates the evolutionary trajectory of Sarvesh Talele's **Slide Deck Builder** skill, progressing from an ephemeral prompt snippet to an enterprise-grade agent skill.

---

## Evolution Stages

### Version 1: Ephemeral Prompt Snippet
**Problem**: The developer needed an AI to format markdown into presentations. They pasted a 40-line prompt into every conversation:
```markdown
Please act as an expert presentation designer. Convert this text into a 5-slide deck.
Use 1 title slide and 4 content slides. For each slide, write a title and 3 bullets.
```
- **Friction**: Every session required re-typing; slide structure varied wildly; no visual output was generated.

---

### Version 2: Ad-Hoc Markdown Instruction (`deck-instructions.md`)
**Progression**: The prompt was saved to a markdown file in the workspace:
```markdown
# Slide Deck Instructions
When asked to build slides, output Marp-compatible markdown with '---' dividers.
Do not use conversational commentary.
```
- **Friction**: Instructions grew to 120 lines; LLMs frequently inserted conversational preambles that broke presentation converters.

---

### Version 3: Bundled Agent Skill (`.agents/skills/deck-builder/`)
**Progression**: Packaged into a formal agent skill with a bundled Python script using `python-pptx`:
```
.agents/skills/deck-builder/
├── SKILL.md
└── scripts/
    └── generate_pptx.py
```
- **Strengths**: Deterministic binary presentation generation directly into `.pptx` files.
- **Friction**: When the model returned malformed slide layouts or missing fields, the Python script crashed with `KeyError`.

---

### Version 4: Validated Tool-Coupled Skill
**Progression**: Added layered configuration and two-phase schema validation with local string salvage:
```
.agents/skills/deck-builder/
├── config.default.yaml
├── SKILL.md
├── CARD.md
├── scripts/
│   ├── generate_pptx.py
│   ├── resolve_config.py
│   └── validate_skill.py
```
- **Strengths**:
  - `config.default.yaml` defines brand palettes, max bullets per slide, and slide aspect ratios.
  - Phase 1 syntactic validation cleans markdown fences and trailing commas locally.
  - Phase 2 semantic validation asserts slide count and layout constraints before invoking `generate_pptx.py`.
  - Visual brief renders slide previews in HTML.

---

### Version 5: Multi-Engine Enterprise Skill
**Progression**: Underwent pre-flight security auditing and registered into the Skill Knowledge Graph:
- **SkillSpector Audit**: Scored **12/100 (SAFE)** — uses only standard file writes and local pptx generation; zero network calls or credentials.
- **Cross-Client Verification**: Validated under `claude-code`, `antigravity`, and `cursor`.
- **Completion Gate**: Full pre-flight verification passed with zero warnings.
