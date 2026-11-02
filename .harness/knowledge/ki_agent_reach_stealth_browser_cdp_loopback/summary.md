# Dedicated Profile Sharing, Anti-Fingerprint Stealth & Localhost CDP Reconnection

## Context & Theoretical Grounding
Spawning clean browser instances on every web request incurs huge latency and triggers anti-bot bot-detection flags. Hijacking the user's primary personal browser risks privacy leaks and tab disruption.

## Distilled Mental Models & Heuristics
1. **Dedicated Isolated Profile**:
   - Stored strictly under `~/.agent-reach/browser/profile`, completely isolated from personal Chrome/Edge user data.
2. **Anti-Fingerprinting Stealth**:
   - `CloakBrowser` overrides `navigator.webdriver`, canvas fingerprints, and WebGL telemetry before page scripts load.
3. **Local Loopback CDP Protocol (127.0.0.1)**:
   - All browser automation commands communicate directly with the local DevTools port via raw HTTP/WebSocket JSON (`cdp.py`), never proxying loopback traffic.
4. **Lifecycle Self-Reclamation**:
   - A background watcher process monitors browser activity; if no agent requests arrive for 600 seconds, the browser shuts down cleanly to release RAM and proactor handles.

## Anti-Pattern Defenses
- **Hijacking Personal User Browsers**: Connecting agent automation directly to the user's active workstation browser profile.
- **Zombie Browser Leaks**: Leaving headless Chromium processes running indefinitely in the background after agent task completion.
