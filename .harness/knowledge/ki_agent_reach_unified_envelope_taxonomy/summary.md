# Schema v1 Result Envelope & Granular Error Classification for Agent Loops

## Context & Theoretical Grounding
AI agents interacting with the public web frequently crash or hallucinate when upstream websites return unexpected HTML errors, cloudflare blocks, or broken DOM structures. `agent-reach` standardizes all channel outputs into an immutable, versioned JSON envelope.

## Distilled Mental Models & Heuristics
1. **The Invariable Result Shape**:
   - Every CLI or Python call returns `{schema_version: 1, ok: bool, channel: str, action: str, backend: str, items: list, meta: dict, error: dict}`.
   - Agents never branch on raw scraping output; they strictly branch on `ok` and `error.code`.
2. **Deterministic Error Categorization**:
   - `FINAL_CODES` (`NOT_FOUND`, `BAD_INPUT`, `PLATFORM_BLOCKED`, `RATE_LIMITED`, `NEED_LOGIN`, `BUSY`) explicitly instruct the agent loop that trying another backend will not succeed, preventing futile retry loops.
   - Retryable codes (`TIMEOUT`, `UPSTREAM_BROKEN`, `NEED_SETUP`) trigger automatic fallback cascades.
3. **Transparent Remediation Hints**:
   - Errors carry a structured `hint` field (e.g. `agent-reach add <tool>` or `agent-reach login <platform>`) allowing ReAct agents to self-heal missing dependencies.

## Anti-Pattern Defenses
- **Raw Web Scraping Output**: Dumping unparsed HTML or noisy terminal stdout directly into LLM context.
- **Ambiguous Failure Handling**: Treating platform rate limits or login walls as generic 500 errors, leading to infinite retry loops.
