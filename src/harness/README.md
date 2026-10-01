# Harness Core Framework (`harness`)

The `harness` package provides the core micro-kernel architecture, IoC container, ReAct execution engine, and plugin runtime for building autonomous, sandboxed AI agent systems.

---

## Architecture & Design Principles

Brain Harness is constructed on strict architectural invariants:
- **Everything is a Plugin (Rule 1)**: All capabilities—model providers, tools, storage adapters, and agent loops—are plugins registered into a hierarchical dependency injection (IoC) container.
- **Typed Service Keys (Rule 2)**: Service resolution is strictly type-safe via generic `ServiceKey[T]` identifiers (`context.require(KEY)` or `context.provide(KEY, instance)`).
- **Transactional Step Isolation (Rule 8)**: Agent tool invocations execute inside atomic context transactions with automated Git rollback on failure.
- **Subprocess Isolation by Default (Rule 5)**: Untrusted external plugins execute in sandboxed subprocess virtual environments with bounded IPC pipes.
- **Immutable Append-Only Events (Rule 4)**: The event bus preserves an immutable audit log of all system transitions and agent observations.

---

## Subpackages

| Package | Description | Core Seam / Protocol |
|---|---|---|
| [`agent/`](agent/README.md) | ReAct execution engine, swarm orchestrator, and pre-LLM context optimization. | `StepExecutionEngine`, `AgentSessionManager`, `ContextOptimizer` |
| [`bridges/`](bridges/README.md) | Bidirectional bridge abstractions connecting external repos and foreign harnesses. | `BaseBridgeAdapter`, `BridgeContext` |
| [`commands/`](commands/README.md) | Single-source Click CLI hierarchy and headless diagnostic entrypoints. | `@main.group()`, `HarnessCliContext` |
| [`creator/`](creator/README.md) | Autonomous plugin and skill generators, AST archetypes, and multi-stage validators. | `PluginCreator`, `PluginValidator`, `ArchetypeRegistry` |
| [`events/`](events/README.md) | Append-only event bus, structured domain events, and reactive async subscriber protocols. | `EventBus`, `EventSubscription`, `DomainEvent` |
| [`ingestion/`](ingestion/README.md) | Binary byte-offset corpus seeker, multi-format doc parsing, and OpenAPI translators. | `DocumentSeeker`, `OpenApiConverter`, `IngestionPipeline` |
| [`kernel/`](kernel/README.md) | Micro-kernel IoC container, lifecycle DAG solver, and state reconciler. | `ServiceContext`, `ServiceKey`, `PluginLifecycleManager` |
| [`mcp/`](mcp/README.md) | Model Context Protocol (MCP) tool integration, server adapters, and JSONSchema validation. | `McpServerAdapter`, `McpToolRegistry` |
| [`plugins/`](plugins/README.md) | Plugin discovery, sandbox proactors, dependency DAG ordering, and virtualenv staging. | `HarnessPlugin`, `SubprocessSandbox`, `PluginLoader` |
| [`services/`](services/README.md) | 70+ typed service protocols and `ServiceKey[T]` registries powering the micro-kernel. | `SERVICE_REGISTRY`, `ServiceKey[T]` |
| [`ui/`](ui/README.md) | Real-time terminal projection, SSE event stream server, and web dashboard. | `TerminalProjection`, `DashboardServer` |

---

## Runtime Bootstrap Example

```python
import asyncio
from harness.kernel.runtime import HarnessRuntime
from harness.services.workspace import WORKSPACE_SERVICE_KEY

async def bootstrap():
    # Initialize micro-kernel runtime with discovered plugins
    async with HarnessRuntime.create() as runtime:
        ctx = runtime.context
        
        # Resolve core micro-kernel services via typed keys
        workspace = ctx.require(WORKSPACE_SERVICE_KEY)
        print(f"Harness active in workspace: {workspace.root_path}")

if __name__ == "__main__":
    asyncio.run(bootstrap())
```

---

## Related Documentation

- [Getting Started Tutorial](../../docs/TUTORIAL.md)
- [How-To Guides](../../docs/HOWTO.md)
- [Architecture Explanation](../../docs/EXPLANATION.md)
- [Kernel Reference](../../docs/reference/kernel.md)
- [Services Reference](../../docs/reference/services.md)
- [CLI Reference](../../docs/reference/cli.md)
