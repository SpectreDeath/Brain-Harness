# Verification Standard — Isolated Plugin Sandboxing

## Problem
Untrusted plugins fetched from GitHub execute code in the harness kernel. A malicious or buggy plugin can corrupt state, exfiltrate data, or crash the runtime.

## Solution
Enforce isolation at registration time via plugin.json:
- `isolation: "subprocess"` for all external/GitHub-sourced plugins (default).
- `isolation: "in_process"` only for explicitly trusted, audited plugins.
- `trusted: true` requires human approval and should be rare.

## Operational Guideline
During plugin validation (`creator validate`), check that:
1. `isolation` is declared explicitly in plugin.json.
2. `trusted` is false unless the plugin author is audited.
3. Sandboxed plugins cannot access kernel services without explicit `requires` declarations.

## Provenance
- Source brain: `antigravity_core`
- Primary source: `df403b28-75e0-43d6-a678-3d15ad63e3bc.system_generated/logs/transcript_full.jsonl#L49`
- Distilled from: AGENTS.md authorship, plugin card standardization request