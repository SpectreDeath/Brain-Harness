# Three-Tier Dynamic Model Switching & Resilient Fallbacks

**ID:** `ki_njoku_dynamic_model_routing`  
**Category:** `agent_orchestration`  
**Origin:** *How to Build AI Applications That Switch Models Automatically* (Chidiebere Njoku)  
**Provenance Lineage:** freeCodeCamp, 2026.

## Executive Summary
Relying on a single frontier AI model for all requests creates severe production vulnerabilities: single-point-of-failure API outages, excessive costs for trivial queries, and degraded throughput. A production AI engine must implement a 3-tier dynamic routing lifecycle separating intent classification, dynamic model selection, and automated fallback chains.

### The 3-Tier Lifecycle Architecture
1. **Tier 1: Prompt Complexity & Intent Analysis**:
   - Fast deterministic analysis (or lightweight model call) evaluating input token length, semantic intent, structural ambiguity, and required reasoning depth.
   - Categorizes task into discrete complexity tiers:
     - *Low*: Simple formatting, FAQ retrieval, classification, text extraction.
     - *Medium*: Multi-turn conversational logic, standard tool calling, structured JSON output.
     - *High*: Deep mathematical reasoning, complex multi-file code refactoring, ambiguous strategic planning.
2. **Tier 2: Dynamic Model Routing Logic**:
   - Routes requests dynamically to the optimal model based on tier, cost budget, and latency constraints:
     - Low tier $\rightarrow$ High-speed, low-cost flash models (Gemini Flash, Claude Haiku).
     - Medium tier $\rightarrow$ Balanced models.
     - High tier $\rightarrow$ Frontier reasoning models with extended thinking budgets (Claude 3.7 Sonnet Thinking, Gemini 3.8 Flash High).
3. **Tier 3: Automatic Fallbacks & Circuit Breakers**:
   - Implements automated provider rollover when primary model calls fail due to HTTP 429 (rate limits), 503 (service downtime), or structural parsing errors.
   - Integrates exponential backoff with jitter and circuit breaker mechanisms to prevent cascading downstream failures.

## Architectural Invariants & Rules
1. **Zero Single-Model Coupling**: Production agent architectures must never hardcode a single model provider without defining at least one viable fallback provider in the harness.
2. **Tier 1 Cost Threshold**: Fast/cheap models must handle $\ge 60\%$ of routine traffic (retrieval, intent parsing, summarization) to preserve token budget for high-reasoning tasks.
