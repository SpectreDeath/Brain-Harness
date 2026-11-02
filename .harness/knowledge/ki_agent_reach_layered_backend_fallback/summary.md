# Deterministic Multi-Tier Backend Fallback Cascades

## Context & Theoretical Grounding
Single-backend web scrapers are fragile against anti-bot challenges, API deprecations, and network timeouts. Agent Reach decouples user actions from specific backends by declaring ordered fallback cascades.

## Distilled Mental Models & Heuristics
1. **Tiered Fallback Ordering**:
   - **Tier 1 (Public API)**: Zero-credential, low-latency REST endpoints or public JSON feeds.
   - **Tier 2 (Stealth Browser)**: CloakBrowser running locally over CDP to bypass basic JavaScript challenges.
   - **Tier 3 (Native Tool / Authenticated CLI)**: Upstream authenticated command-line utilities.
2. **Adaptive Circuit Breakers**:
   - `BACKEND_PAUSE_SECONDS` (`TIMEOUT: 60s`, `UPSTREAM_BROKEN: 120s`, `NEED_SETUP: 60s`, `RATE_LIMIT_SECONDS: 3600s`) pauses failing backends in shared state, skipping them in subsequent calls to maintain low latency.
3. **Slot Lock Arbitration**:
   - Concurrency for browser-dependent backends is guarded by slot locks (`wait_lock`, `query_slot`), preventing multiple agent steps from thrashing a single browser tab.

## Anti-Pattern Defenses
- **Static Single-Backend Binding**: Hardcoding scraping actions to a single fragile DOM selector.
- **Unbounded Throttled Retries**: Repeatedly hitting rate-limited endpoints without adaptive circuit breaking.
