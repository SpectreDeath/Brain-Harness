# Headless CLI Session DAG Inspection & Export (`ki_self_20260827_03`)

## Summary
Session graphs, multi-agent trace logs, and context AST trees must be fully navigable in headless CLI environments without relying on visual IDEs or web UIs.

## Architectural Invariant
1. **Unified Click Surface:** Subcommands `harness session tree` and `harness session export` provide ANSI ASCII tree rendering and structured JSON streaming.
2. **Deterministic Replayability:** Exported session trees carry complete event IDs, tool execution receipts, and token consumption statistics.
3. **MCP Parity:** Every CLI introspection command maps directly to a typed MCP tool endpoint for seamless agent-to-agent delegation.

## Provenance
- Implemented and verified in Architecture Deepening Cycle 10.
