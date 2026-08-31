### Distilled Heuristic
CLI command groups (e.g. '@main.group("bridge")') must be declared exactly once in a single co-located block to prevent later definitions from shadowing subcommands and breaking CLI test assertions.

### Named Anti-Pattern
Redefining CLI command groups at the bottom of cli.py.

### Empirical Evidence & Provenance
- **Sources**: architecture-review-20260826-harness-reflector.html, architecture-review-20260826.html, architecture-review-20260825-memory-epistemics.html, architecture-review-20260825-integration-io.html, architecture-review-1787664067.html, architecture-review-20260824-172700.html, architecture-review-20260823-165800.html, architecture-review-20260823-154200.html
- **Confidence**: 99%
