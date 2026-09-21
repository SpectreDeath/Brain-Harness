# Skill Summary Card: `uncertainty-aware-ai-architect`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:       uncertainty-aware-ai-architect            │
│ Category:    agent_orchestration / uncertainty-guard   │
│ Invocation:  /uncertainty-aware-ai-architect           │
│ Trigger:     "build uncertainty aware AI",             │
│              "prevent LLM overconfidence",             │
│              "RAG retrieval quality scoring",          │
│              "token logprob uncertainty",              │
│              "hallucination boundary gate"             │
│ Version:     1.0.0                                     │
│ Provides:    "uncertainty_interception_engine"         │
│ Requires:    "book-to-skill-forge", "crafting-skills"  │
├────────────────────────────────────────────────────────┤
│ Target:      Architect and audit uncertainty-aware AI  │
│              and RAG pipelines with deterministic      │
│              mathematical boundaries and HITL routing. │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Operational Progression

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Boundary Formulation** | Encode operational domains and evaluate input cosine similarity | Boundary centroid vectors | Out-of-scope queries rejected at perimeter (Sim < 0.45) |
| **2. Retrieval Scoring** | Compute cosine similarity between query and retrieved document chunks | Chunk relevance scores | Insufficient context blocked from prompt (Sim < 0.60) |
| **3. Logprob Validation** | Calculate sequence mean logprob and perplexity from API payloads | Logprob certainty report | Low certainty completions intercepted (Avg < -0.35) |
| **4. Pipeline Orchestration** | Unify 3 verification layers into deterministic enterprise lifecycle | Orchestration Engine | Fallbacks routed to HITL and ticketing queues |
| **5. Continuous Calibration** | Aggregate under-retrieved queries and calibrate vector thresholds | Telemetry & Gap Report | Zero prompt self-confidence; thresholds re-tuned |

---

## The Three Pillars Cheat Sheet

### 1. The Visual Brief (Temp HTML + Mermaid)
```html
<!-- Location: %TEMP%\uncertainty-pipeline-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto">
  <!-- 3-Layer Interception Mermaid DAG & Threshold Scorecards -->
</body>
</html>
```

### 2. The Mandatory Checkpoint (`RequestFeedback: true`)
```markdown
# Implementation Plan
Set `RequestFeedback: true` in artifact metadata.
Agent MUST STOP and wait for explicit human approval before deploying boundary gates.
```

### 3. Explicit Anti-Patterns Box
- **Prompted Self-Confidence**: Asking the model "Are you sure?" in prompts rather than evaluating mathematical logprobs.
- **Context Flooding on Low Retrieval**: Feeding irrelevant chunks into context when top match score is below threshold.
- **Silent Fallback Concealment**: Treating "I don't know" as a runtime crash instead of an operational success state.
- **Static Uncalibrated Thresholds**: Hardcoding similarity cutoffs without validating against query length and corpus vocabulary.
- **Bypassing Upstream Gates**: Skipping input domain checks and relying exclusively on expensive downstream generation checks.

---

## Verification & Quality Checklist

- [ ] **Positive Phrasing**: Instructions state direct target actions instead of negative prohibitions.
- [ ] **Leading Words**: Employs compact domain vocabulary (*boundary*, *centroid*, *cosine*, *logprob*, *perplexity*, *escalation*).
- [ ] **Exhaustive Completion Criteria**: Every stage specifies unambiguous mathematical completion gates.
- [ ] **Modular Boundaries**: Clear separation between boundary detection, retrieval scoring, and logprob validation.
- [ ] **Companion Card Present**: Co-located `CARD.md` authored with ASCII single-pipe metadata box.
- [ ] **Pre-Flight Validation**: Passes `SkillValidator.validate()` with zero errors or warnings.
