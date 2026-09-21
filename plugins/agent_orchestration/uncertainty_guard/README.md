# UncertaintyGuard Plugin (`plugin.uncertainty_guard`)

Deterministic 3-layer uncertainty interception, semantic distance gating, token logprob entropy analysis, and Human-In-The-Loop escalation based on Chidiebere Njoku's foundational framework (*How to Build AI Systems That Know When They Don't Know: A Practical Guide*, 2026), grounded in `ki_njoku_uncertainty_aware_systems`.

---

## 1. Overview & Architecture

Large Language Models predictably fail when asked questions outside their training boundaries or when supplied with low-quality, incomplete context. System prompts instructing models to *"only answer if 100% sure"* do not prevent hallucinations because generation log probabilities remain uncalibrated against real-world truth.

`plugin.uncertainty_guard` implements a **3-Layer Request Interception Lifecycle**:
1. **Layer 1: Input Boundary Gating (`verify_boundary`)**: Evaluates query cosine alignment against authorized domain centroids. Requests below threshold ($\tau_{\text{boundary}} = 0.45$) are rejected immediately at the perimeter with $0 token spend.
2. **Layer 2: Retrieval Quality & Semantic Distance Scoring (`score_retrieval`)**: Calculates cosine similarity across retrieved document chunks. When top relevance fails threshold ($\tau_{\text{retrieval}} = 0.60$), context chunks are blocked from prompt injection and the request is escalated to HITL support.
3. **Layer 3: Probabilistic Logit Analysis & Output Validation (`validate_logprobs`)**: Analyzes token generation log probabilities from model API responses ($\tau_{\text{logprob}} = -0.35$). If mean logprob drops or text perplexity surges ($\exp(-\bar{L})$), the completion is suppressed in favor of safe fallback.

---

## 2. Quick Start & Tutorial

### In-Memory IoC Resolution (ReAct Step Loops)

```python
from harness.kernel.context import ServiceContext
from harness.services.uncertainty_guard import UNCERTAINTY_GUARD_SERVICE_KEY

# Resolve from IoC container
guard_svc = context.require(UNCERTAINTY_GUARD_SERVICE_KEY)

# Execute unified 3-layer request interception
result = guard_svc.intercept_request(
    query="How do I reset my VPN password?",
    retrieved_chunks=[
        "To reset your corporate VPN password, visit auth.internal.corp..."
    ],
    token_logprobs=[-0.12, -0.08, -0.21, -0.05],
    draft_response="Visit auth.internal.corp to reset your VPN credentials.",
)

if result.state == "PASSED_VERIFIED":
    print("Delivering response:", result.response_text)
else:
    print(f"Interception triggered [{result.state}]:", result.response_text)
```

---

## 3. How-To Guides

### Running via Headless Click CLI

```bash
# Test Layer 1 domain perimeter
harness uncertainty gate -q "What is the capital of Mars?"

# Score retrieved documentation chunks
harness uncertainty retrieval -q "Configure VPN" -c "VPN setup instructions..." -c "Unrelated file..."

# Verify token logprobs and perplexity
harness uncertainty logprobs -l -0.15 -l -0.22 -l -0.18

# Execute full 3-layer pipeline
harness uncertainty pipeline -q "Configure VPN" -c "VPN doc..." -l -0.1 -r "Instructions here"
```

---

## 4. Configuration Reference

Configuration lives in `config.default.yaml`:

```yaml
version: "1.0.0"

boundary:
  similarity_threshold: 0.45
  timeout_ms: 10.0

retrieval:
  minimum_relevance: 0.60
  max_chunks_to_score: 20
  timeout_ms: 25.0

logprob:
  logprob_threshold: -0.35
  max_perplexity: 1.42

telemetry:
  escalation_queue_max_size: 1000
  cluster_min_size_for_debt: 2
```
