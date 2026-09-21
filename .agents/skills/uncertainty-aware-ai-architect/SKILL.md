---
name: uncertainty-aware-ai-architect
description: Architect, implement, and audit uncertainty-aware AI and RAG systems using 3-layer deterministic boundaries: semantic domain gating, retrieval quality scoring, and probabilistic logit entropy analysis. Do not use for generic prompt formatting or uncalibrated prompt-only guardrails.
---

# Uncertainty-Aware AI Architect: Deterministic Boundary & Confidence Engine

`uncertainty-aware-ai-architect` is the cognitive and architectural engine for designing, implementing, calibrating, and auditing uncertainty-aware AI and Retrieval-Augmented Generation (RAG) systems. Originating from Chidiebere Njoku's foundational framework (*How to Build AI Systems That Know When They Don't Know: A Practical Guide*), it solves the **Overconfidence Vulnerability** by wrapping Large Language Models in deterministic, mathematical request interception gates rather than relying on uncalibrated, prompt-driven self-reporting.

Standard LLMs lack an intrinsic mechanism to output "I don't know." When presented with out-of-scope prompts or unindexed documents, naive systems treat missing context as a text-completion puzzle to solve at all costs—yielding confident hallucinations. Instructing models via system prompts like *"Only answer if you are 100% sure"* is demonstrably ineffective. `uncertainty-aware-ai-architect` enforces a **3-Layer Request Interception Lifecycle** where "I don't know" is an intentional, successful operational state routed to Human-In-The-Loop (HITL) queues.

Every uncertainty architecture session executes this five-stage progression:

```
[1. Input Domain & Boundary Formulation] → [2. Retrieval Quality Scoring] → [3. Probabilistic Logit Analysis] → [4. Orchestration & Escalation] → [5. Continuous Calibration & Gap Mining]
```

See [CARD.md](CARD.md) for the companion summary card, 5-stage reference matrix, and verification checklist.
Consult [book-to-skill-forge](../book-to-skill-forge/SKILL.md) for literature synthesis standards, [crafting-skills](../crafting-skills/SKILL.md) for deep-module craft, and [compute-model-assessor](../compute-model-assessor/SKILL.md) for dynamic thinking budgets.

---

## 1. Input Domain & Boundary Formulation

Define and encode authorized operational domain parameters to intercept and reject out-of-scope user queries before triggering expensive retrieval pipelines or model API invocations:

1. **Define Domain Boundary Centroids**:
   - Explicitly list approved operational topics (e.g. `"company VPN configuration"`, `"employee payroll schedules"`, `"internal IT software deployment"`).
   - Generate normalized semantic vector embeddings for each domain centroid using a lightweight embedding model (e.g., `all-MiniLM-L6-v2`).
2. **Execute Cosine Similarity Gating**:
   - Compute the cosine similarity between the incoming user query vector $q$ and all domain centroid vectors $D$:
     $$	ext{Sim}(q, d_i) = \frac{q \cdot d_i}{\|q\| \|d_i\|}$$
   - Take the maximum alignment score: $S_{\text{boundary}} = \max_i \text{Sim}(q, d_i)$.
3. **Enforce Boundary Rejection Cutoff**:
   - Compare $S_{\text{boundary}}$ against the calibrated boundary threshold (default $\tau_{\text{boundary}} = 0.45$).
   - If $S_{\text{boundary}} < \tau_{\text{boundary}}$, immediately reject the request with a structured rejection payload:
     `{"is_valid": False, "score": S_boundary, "reason": "Query falls outside operational domain boundaries."}`.
   - Halt execution immediately. Zero tokens or vector queries are dispatched downstream.

> **Completion criterion**: Operational domain topics encoded into vector embeddings, cosine gating evaluated on input queries, and out-of-scope requests rejected at the perimeter.

---

## 2. Retrieval Quality & Semantic Distance Scoring

Prevent model hallucinations caused by low-relevance or missing documentation by scoring retrieved context chunks against the query before context injection:

1. **Vector Document Retrieval & Cosine Evaluation**:
   - Ingest retrieved document chunks $C = \{c_1, c_2, \dots, c_k\}$ returned by the vector database.
   - Encode query $q$ and retrieved chunks $c_j$ into the same embedding space.
   - Compute pairwise cosine similarity scores between the query and each retrieved chunk:
     $$S_{\text{chunk}}(j) = \frac{q \cdot c_j}{\|q\| \|c_j\|}$$
2. **Top-Match Sufficiency Gating**:
   - Identify the highest relevance score: $S_{\text{retrieval}} = \max_j S_{\text{chunk}}(j)$.
   - Evaluate against the calibrated ground-truth relevance threshold (default $\tau_{\text{retrieval}} = 0.60$).
3. **Escalation & Document Blocking**:
   - If $S_{\text{retrieval}} < \tau_{\text{retrieval}}$, flag context as insufficient.
   - Block context chunks from entering prompt context to prevent hallucinated connections.
   - Trigger the support escalation branch with metadata:
     `{"has_context": False, "top_score": S_retrieval, "action": "ESCALATE_TO_SUPPORT"}`.

> **Completion criterion**: Retrieved document chunks scored via cosine similarity, minimum relevance threshold enforced, and insufficient contexts blocked from prompt injection.

---

## 3. Probabilistic Logit Entropy & Output Validation

Detect generation uncertainty at the token level by mathematically inspecting generation log probabilities (`logprobs`) returned in model API payloads:

1. **Extract Token Log Probabilities**:
   - Configure model API requests with logprob tracking enabled (e.g. `logprobs=True, top_logprobs=5`).
   - Extract the sequence of chosen token log probabilities: $L = [\log p_1, \log p_2, \dots, \log p_N]$.
2. **Calculate Average Logprob & Perplexity**:
   - Compute the mean sequence log probability:
     $$\bar{L} = \frac{1}{N} \sum_{i=1}^N \log p_i$$
   - Compute sequence text perplexity:
     $$\text{Perplexity} = \exp(-\bar{L})$$
3. **Evaluate Output Certainty Threshold**:
   - Compare $\bar{L}$ against the calibrated logprob threshold (default $\tau_{\text{logprob}} = -0.35$).
   - If $\bar{L} < \tau_{\text{logprob}}$ (or perplexity surges), flag the generation as an uncertain completion:
     `{"is_confident": False, "avg_logprob": round(avg_logprob, 4), "perplexity": round(perplexity, 4)}`.
   - Suppress unconfident generation and route to safe fallback.

> **Completion criterion**: Token log probabilities extracted, mean logprob and perplexity computed mathematically, and generations below confidence threshold intercepted.

---

## 4. Deterministic Pipeline Orchestration & Fallback Routing

Unify the three defensive layers into an end-to-end deterministic enterprise request lifecycle:

1. **Sequential Interception Gate Execution**:
   - **Gate 1 (Perimeter)**: Call `BoundaryDetector.verify_domain_relevance(query)`. If failed $\rightarrow$ return immediate rejection.
   - **Gate 2 (Evidence)**: Call `RetrievalQualityScorer.evaluate_retrieved_context(query, docs)`. If failed $\rightarrow$ dispatch to support ticketing and log knowledge gap.
   - **Gate 3 (Verification)**: Execute model generation; inspect token logprobs via `OutputLogprobValidator.evaluate_token_certainty(logprobs)`. If failed $\rightarrow$ trigger calibrated fallback response.
2. **Intentional Escalation Routing**:
   - Treat "I don't know" as an operational success state rather than an unhandled application exception.
   - Route rejected or low-confidence queries to dedicated support channels or Human-In-The-Loop (HITL) review queues.
3. **Synthesize The Visual Brief**:
   - When introducing or tuning uncertainty pipelines, generate an interactive HTML Visual Brief in `%TEMP%` (e.g. `%TEMP%\uncertainty-pipeline-<timestamp>.html`) containing the Mermaid request lifecycle DAG, current threshold configurations, and failure mode statistics.

> **Completion criterion**: End-to-end request lifecycle orchestrating the 3 verification layers sequentially with deterministic fallback dispatch and visual brief generation.

---

## 5. Continuous Calibration & Documentation Gap Telemetry

Maintain long-term system calibration through continuous telemetry aggregation and threshold tuning:

1. **Decouple Confidence from System Prompts**:
   - Enforce zero reliance on prompt-instructed self-confidence. Use mathematical indicators exclusively.
2. **Mine Retrieval Failures for Knowledge Debt**:
   - Aggregate all requests that fail Layer 2 retrieval scoring ($S_{\text{retrieval}} < 0.60$).
   - Cluster failed queries to identify missing, outdated, or poorly indexed corporate documentation.
   - Automatically scaffold documentation backlog tickets for knowledge gaps.
3. **Tune Thresholds on Production Query Drift**:
   - Embedding distances fluctuate based on document length, vocabulary specialization, and query conciseness.
   - Periodically evaluate holdout verification sets from production logs to re-calibrate $\tau_{\text{boundary}}$ and $\tau_{\text{retrieval}}$ for precision-recall trade-offs.

> **Completion criterion**: Under-retrieved queries aggregated into knowledge gap telemetry, thresholds periodically calibrated against real-world distributions, and prompt-based self-confidence eliminated.

---

## Diagnostic Evaluation Scorecard

| Evaluation Axis | Diagnostic Inquiry | Verification Metric | Passing Standard |
|---|---|---|---|
| **1. Boundary Pre-Gating** | Are queries tested against domain bounds before retrieval or model invocation? | $\max_i \text{Sim}(q, d_i)$ | $\ge 0.45$; halts immediately on failure without downstream token spend |
| **2. Context Sufficiency** | Does the pipeline verify retrieved chunks before feeding them to LLM context? | $\max_j \text{Sim}(q, c_j)$ | $\ge 0.60$; escalates to HITL when evidence is insufficient to answer |
| **3. Probabilistic Output Audit** | Are generation log probabilities inspected mathematically rather than prompt-asked? | $\bar{L}$ & $\exp(-\bar{L})$ | $\ge -0.35$ avg logprob; fallback triggered if entropy surges |
| **4. Intentional Escalation** | Is "I don't know" treated as an operational success state with clear routing? | Routing Contract & Payload | Dedicated ticketing / review queue dispatch without 500 crashes |
| **5. Telemetry & Gap Mining** | Are low-relevance retrieval failures logged and mined to uncover missing docs? | Audit Log Aggregation | Automated documentation debt tickets generated from repeated misses |

---

## Reference Architecture & Deepened Seams

The capability is elevated into an authoritative micro-kernel service seam and slotted domain engine compliant with **Rule 49 (Skill-to-IoC Micro-Kernel Seam Elevation Invariant)**.

### 1. In-Memory Micro-Kernel IoC Resolution

```python
from harness.kernel.context import ServiceContext
from harness.services.uncertainty_guard import UNCERTAINTY_GUARD_SERVICE_KEY

# Resolve UncertaintyGuardService from IoC container
guard_svc = context.require(UNCERTAINTY_GUARD_SERVICE_KEY)

# Execute unified 3-layer request interception
result = guard_svc.intercept_request(
    query="Configure corporate VPN",
    retrieved_chunks=["Corporate VPN setup instructions..."],
    token_logprobs=[-0.12, -0.08, -0.15],
    draft_response="Follow the standard VPN profile setup."
)

if result.state == "PASSED_VERIFIED":
    print("Delivered response:", result.response_text)
else:
    print(f"Interception [{result.state}]:", result.response_text)
```

### 2. Standalone Slotted Domain Engine (`uncertainty_guard_engine.py`)

The underlying engine ([`uncertainty_guard_engine.py`](scripts/uncertainty_guard_engine.py)) uses slotted and frozen dataclasses ([`Rule 12`](../../AGENTS.md), [`Rule 43`](../../AGENTS.md)) with zero-dependency sub-millisecond cosine vectorization:

```python
from scripts.uncertainty_guard_engine import UncertaintyGuardEngine

engine = UncertaintyGuardEngine()

# Layer 1: Boundary check (<1ms)
b_res = engine.verify_boundary("Where is the lunchroom?")
assert not b_res.is_valid  # Out-of-scope rejected at perimeter

# Layer 2: Retrieval scoring (tau = 0.60)
r_res = engine.score_retrieval("Configure VPN", ["VPN client installation..."])
assert r_res.has_sufficient_context

# Layer 3: Output Logprob validation (tau = -0.35)
l_res = engine.validate_logprobs([-0.1, -0.05, -0.2])
assert l_res.is_confident
```

### 3. Headless Click CLI Inspection

```bash
# Test Layer 1 domain perimeter
harness uncertainty gate -q "Configure VPN connection"

# Score retrieved context chunks
harness uncertainty retrieval -q "VPN access" -c "VPN config..." -c "Payroll..."

# Audit generation logprobs & perplexity
harness uncertainty logprobs -l -0.15 -l -0.20 -l -0.10

# Run full 3-layer request lifecycle
harness uncertainty pipeline -q "Configure VPN" -c "VPN setup doc" -l -0.1

# Cluster under-retrieved queries to uncover missing documentation debt
harness uncertainty calibrate -q "401k match policy" -q "401k contribution limits"
```


---

## Anti-Patterns

- **Prompted Self-Confidence** — Asking the model "Are you confident?" inside system prompts; uncalibrated models hallucinate high confidence.
- **Context Flooding on Low Retrieval** — Passing low-scoring, irrelevant document chunks into the LLM context, forcing the model to hallucinate connections.
- **Silent Fallback Concealment** — Treating an "I don't know" as an unhandled error or generic 500 failure instead of an intentional operational escalation.
- **Static Uncalibrated Thresholds** — Setting rigid cosine similarity thresholds without testing across document lengths, query lengths, and domain vocabularies.
- **Bypassing Upstream Gates** — Relying exclusively on output evaluation while skipping input domain boundary checks, wasting compute and API budgets.
