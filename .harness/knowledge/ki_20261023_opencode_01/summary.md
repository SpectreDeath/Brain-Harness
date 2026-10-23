# Unidirectional Layered Monorepo Architecture in AI Harnesses

## Context
In large AI agent harnesses combining CLI tools, terminal user interfaces (TUIs), background daemon servers, local SQLite persistence, and provider client SDKs, circular dependencies and improper module coupling frequently lead to credential exposure, bloated client bundles, and broken test harnesses.

## Distilled Learning
Enforce a strict, unidirectional acyclic dependency graph across the monorepo layers:
- `packages/schema`: Contains pure data definitions (Effect Schema / Pydantic models). Zero dependencies on runtime engines.
- `packages/core` & `packages/protocol`: Encapsulate core agent execution, tools, PTY, and OpenAPI specifications. Depend strictly on `schema`.
- `packages/server`: Implements background HTTP/WebSocket daemons, authentication, and database persistence. Depends on `core` and `protocol`.
- `packages/client`, `packages/cli`, `packages/tui`: User-facing presentation and client wrappers. They may depend on `schema` and `protocol`, but NEVER directly on `core` or `server`.
- `packages/sdk`: Clean composition facade exposing client and server bindings for external consumers.

## Triggers & Seam Choices
- **Trigger**: Partitioning multi-package repositories or micro-kernel agent architectures.
- **Seam Choice**: Enforce dependency directionality via automated static AST linters (`ast-grep` / `import/no-restricted-paths`) in pre-commit and CI gates.
