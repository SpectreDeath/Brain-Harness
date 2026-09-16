# Dynamic oRPC-to-OpenAPI Schema Pipeline with First-Class MCP Tool Annotations

## Epistemic Introspection & Overview

ChatbotX implements a unified API-to-Agent bridge: instead of manually authoring and synchronizing REST endpoints, OpenAPI specs, CLI commands, and Model Context Protocol (MCP) tools in parallel, all API contracts originate as **oRPC** routers (`apps/builder/src/routers/public.ts`).

From these typed TypeScript procedure definitions, ChatbotX dynamically compiles:
1. HTTP REST endpoints served under `/api/*`
2. An OpenAPI 3.1 schema served at `/api/public-spec.json` with conditional ETag caching
3. Dynamic CLI commands via dynamic parameter introspection (`apps/cli/src/openapi-loader.ts`)
4. Native MCP tools for AI agents via stdio and SSE transports (`apps/mcp-server/src/openapi-loader.ts`)

---

## The oRPC-to-OpenAPI Synthesis Architecture

```
[52 oRPC Sub-Routers]
         │
         ▼
[publicRouter Consolidation] (apps/builder/src/routers/public.ts)
         │
         ▼
[OpenAPIGenerator + ZodToJsonSchemaConverter] (apps/builder/src/app/api/public-spec.json/route.ts)
         │
         ├──► [In-Process Cache: TTL 300s, ETag SHA-1]
         ▼
[/api/public-spec.json Endpoint]
         │
         ├──► [ChatbotX CLI: dynamic-executor.ts]
         └──► [ChatbotX MCP Server: create-mcp-server.ts]
```

### Key Engineering Decisions:

1. **In-Process Spec Caching**: Generating OpenAPI specifications from 52 feature routers and Zod schemas takes significant CPU time. ChatbotX caches the generated spec string in memory keyed by `tenantName::origin::filter`, returning `304 Not Modified` when `If-None-Match` matches the SHA-1 ETag.
2. **First-Class Agent Hints (`x-mcp`)**: Operations declare behavioral properties:
   - `readOnlyHint: true` — safe for auto-execution without confirmation.
   - `destructiveHint: true` — requires interactive agent approval.
   - `idempotentHint: true` — safe for retry loops on network glitch.
3. **Security Scope Pruning**: Tools requiring channel-level webhooks or user session cookies are rejected at load time; only workspace-token operations (`bearerAuth`, `developerAccessToken`) are promoted to tools.
