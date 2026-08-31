# Tool Package Decoupling

## Context
When an AI agent harness supports diverse capabilities (such as LSP integrations, MCP servers, sandboxed execution environments, and file system operations), maintaining them all in a single monolithic tool registry creates tight coupling, slows down tests, and bloats the dependency graph.

## Distilled Learning
Extract distinct agent capabilities into their own isolated packages within a monorepo structure. Each package (e.g., `packages/mcp`, `packages/lsp`, `packages/sandbox`) should manage its own dependencies, entrypoints, and tests.

## Triggers & Seam Choices
- **Trigger**: When adding a new capability that requires distinct external dependencies (e.g., a specific LSP client library or a Docker sandbox runner).
- **Seam Choice**: Define an interface in a core package (e.g., `packages/core` or `packages/tool-registry`) and implement the capability in a dedicated package that depends on core, rather than adding the capability directly to core.
