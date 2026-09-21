# Deterministic 3-Layer Uncertainty Interception & Overconfidence Mitigation

**ID:** `ki_njoku_uncertainty_aware_systems`  
**Category:** `agent_orchestration`  
**Origin:** *How to Build AI Systems That Know When They Don't Know: A Practical Guide* (Chidiebere Njoku)  
**Provenance Lineage:** freeCodeCamp, 2026.

## Executive Summary

Standard Large Language Models lack an intrinsic calibration mechanism to declare "I don't know." When presented with missing documentation or out-of-scope prompts, models treat missing facts as text-completion puzzles to be solved at all costs, resulting in confident hallucinations. Instructing models via prompt engineering (e.g. *"Only answer if you are 100% sure"*) fails in production because token generation probability distributions remain uncalibrated against real-world truth.

Enterprise AI applications require transition from naive prompt engineering to a security-first engineering mindset. Models must be wrapped inside a **deterministic 3-layer request interception pipeline** that evaluates input intent, document relevance, and generation probabilities independently of the LLM's natural language output. In this architecture, declaring "I don't know" is an intentional, successful operational outcome routed directly to human support and ticketing channels.

---

## The 3-Layer Interception Lifecycle

```
[User Request]
       │
       ▼
[Layer 1: Input Boundary Gate] ──────(Score < 0.45)─────► [Immediate Domain Rejection]
       │ (Score >= 0.45)
       ▼
[Execute Vector Retrieval]
       │
       ▼
[Layer 2: Retrieval Quality Scorer] ──(Score < 0.60)─────► [Escalate to Support & Log Gap]
       │ (Score >= 0.60)
       ▼
[Model API Call with Logprobs]
       │
       ▼
[Layer 3: Output Logprob Validator] ─(Avg < -0.35)──────► [Activate Controlled Fallback]
       │ (Avg >= -0.35)
       ▼
[Verified Response Delivered]
```

### Layer 1: Input Intent & Boundary Detection (`BoundaryDetector`)
- Pre-retrieval defensive perimeter. Converts approved enterprise operational topics into semantic vector embeddings.
- Evaluates query cosine similarity against domain centroids:
  $$\text{Sim}(q, d_i) = \frac{q \cdot d_i}{\|q\| \|d_i\|}$$
- If $\max_i \text{Sim}(q, d_i) < \tau_{\text{boundary}}$ (default 0.45), request is rejected immediately.
- Conserves API compute and eliminates out-of-domain guessing.

### Layer 2: Semantic Distance & Retrieval Quality Scoring (`RetrievalQualityScorer`)
- Context sufficiency verification. Vector databases routinely return low-scoring chunks when relevant documentation is absent.
- Computes cosine similarity across all retrieved document chunks vs query:
  $$\max_j \text{Sim}(q, c_j) < \tau_{\text{retrieval}} \quad (\text{default } 0.60)$$
- If top match fails relevance threshold, chunks are blocked from prompt context and the query is escalated to human support.

### Layer 3: Probabilistic Logit Analysis & Output Validation (`OutputLogprobValidator`)
- Post-generation mathematical verification. When an LLM is unsure, token distribution entropy increases.
- Extracts token log probabilities from model API response payloads:
  $$\bar{L} = \frac{1}{N} \sum_{i=1}^N \log p_i, \quad \text{Perplexity} = \exp(-\bar{L})$$
- If $\bar{L} < \tau_{\text{logprob}}$ (default -0.35), text perplexity surges and the generation is suppressed in favor of safe fallback.

---

## Operational Deployment Invariants

1. **Decouple Confidence Checks from System Prompts**: Never ask the model in natural language whether it is confident. Use mathematical vector distances and API log probabilities.
2. **Intentional Escalation Topologies**: "I don't know" is an operational success state. Route low-confidence requests directly into ticketing queues or Human-In-The-Loop (HITL) channels.
3. **Retrieval Metric Knowledge Mining**: Low-relevance retrieval failures serve as automated telemetry signaling missing, outdated, or poorly indexed documentation.
4. **Dynamic Threshold Calibration**: Continuously calibrate similarity thresholds against production logs to adapt to vocabulary shifts and document length variations.
5. **Ecosystem Lineage**: Bridges directly with `ki_njoku_dynamic_model_routing` (3-tier complexity routing) and `compute-model-assessor` (5-dimensional thinking budgets).
