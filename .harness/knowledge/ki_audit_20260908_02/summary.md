## Compound Topology Invariant

Brain Harness operates as four concurrent topologies layered in composition.
Any architectural decision must satisfy all four simultaneously.

### Topology 1: Graph of Trees
- ServiceContext maintains parent-child scope trees for plugin isolation
- Plugin dependency graph (DAG) is topologically sorted before enabling
- Plugin categories form domain sub-trees (8 categories, 137 plugin files)

### Topology 2: Hash-Indexed Dispatcher
- EventBus._handlers is a dict[str, list[EventHandler]] — O(1) dispatch by event type
- ToolRegistry maps tool names to ToolSpec + executor chain
- ServiceContext._registry maps ServiceKey.name -> ServiceEntry

### Topology 3: Fan-Out / Fan-In Swarm
- SwarmCoordinator executes parallel wave nodes concurrently via asyncio.gather()
- Topology dependency edges drive wave ordering via DependencyGraph
- Borda count / weighted majority voting collapses fan-out results

### Topology 4: Priority Rewake Loop
- StepExecutionEngine tool observations re-inject into agent reasoning context
- Async rewake: background tool results -> queue -> agent step continuation
- EventBus.stream() provides AsyncIterator[HarnessEvent] for live rewake feeds
