# Non-Invasive Scoped Metadata Annotations vs. Core Kernel Mutability

## Architectural Summary
Demonstrates the principle of non-invasive kernel extensibility. Rather than modifying `ServiceContext.__init__` to force a 4-tier scope enum into the core micro-kernel, a standalone `ScopeInspector` traverses existing parent-child chains and annotates each level (`APP` $\rightarrow$ `WORKSPACE` $\rightarrow$ `SESSION` $\rightarrow$ `AGENT`) externally.

## Operational Guidelines
1. **Preserve Kernel Signatures:** Never alter core IoC container signatures for domain-specific features without a dedicated kernel-level RFC.
2. **Adapter-Based Introspection:** Build read-only inspection services that operate over generic parent-child context trees.
3. **Zero Ecosystem Breakage:** Ensure all 50+ existing plugins continue operating without required argument changes.
