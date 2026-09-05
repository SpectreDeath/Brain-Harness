# Harness Hybrid Topology Map

**ID:** `ki-topology-map`

## Summary
Brain Harness employs a hybrid topology: Graph-of-Trees (plugin dependency DAG managing service hierarchies via ScopedServiceContext parent-child chains) composed with Hash-Indexed O(1) Dispatchers (IoC ServiceContext._entries, EventBus._handlers, ToolRegistry._tools) and a DAG Execution Scheduler (DependencyGraph.execution_waves() for lifecycle ordering and swarm parallel execution). Blast radius matrix covers 11 core vertices.
