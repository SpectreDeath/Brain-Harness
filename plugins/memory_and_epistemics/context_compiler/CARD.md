# 🧠 Skill Summary Card: `context_compiler`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        context_compiler                          │
│ Category:    memory_and_epistemics                     │
│ Archetype:   tool_provider / service_provider          │
│ Isolation:   subprocess                                │
│ Status:      Verified & Sandboxed                      │
├────────────────────────────────────────────────────────┤
│ Target:      3-Tier AST Token-Pruning Context Compiler │
└────────────────────────────────────────────────────────┘
```

## Tools
- `compile_context(repo_root, target_file, max_hops=2)`: Compiles 3-tier prompt context with token statistics.
- `skeletonize_code(source_code)`: AST stripper removing executable bodies to `...`.
- `resolve_reachability(repo_root, target_file, max_hops=2)`: Multi-hop dependency and blindspot detector.
- `estimate_token_reduction(repo_root, target_file, max_hops=2)`: Comparative token analysis.
