# Agent Reach Bridge Plugin (`plugin.agent_reach_bridge`)

## Overview
The `agent_reach_bridge` plugin connects the Brain Harness micro-kernel to the **Agent-Reach** ecosystem (`Panniantong/Agent-Reach`), providing AI agents with reliable internet access, walled-garden content extraction, and anti-fingerprint CloakBrowser automation over loopback Chrome DevTools Protocol (CDP).

It registers the `service.agent_reach` key (`AGENT_REACH_SERVICE_KEY`) in the IoC container and exposes tools for:
- Automatic platform channel matching (`youtube`, `github`, `reddit`, `bilibili`, `xiaohongshu`, `boss`, `v2ex`, `web`, etc.).
- Multi-tier fallback cascades: fast public APIs $\rightarrow$ CloakBrowser $\rightarrow$ native session CLIs.
- Schema v1 result envelope normalization with strict error taxonomy.
- Automatic inline basic auth credential redaction.

## Tools
- `reach_read`: Ingest and parse target URL content into Schema v1 envelopes.
- `reach_action`: Dispatch platform-specific actions (e.g. search, comments, repo info).
- `reach_inspect_channels`: List all 11+ supported platform channels, tiers, and capabilities.
- `reach_scrub_url`: Sanitize authentication secrets from URLs.

