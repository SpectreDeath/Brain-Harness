### Distilled Heuristic
External plugins with subprocess/venv isolation must remain in DISCOVERED/VALIDATED state during kernel startup and test execution, provisioning virtual environments lazily on first invocation to eliminate cold-start timeouts.

### Named Anti-Pattern
Eagerly provisioning virtualenvs for all user plugins in HarnessRuntime.start().

### Empirical Evidence & Provenance
- **Sources**: architecture-review-20260826.html, architecture-review-20260824-172700.html
- **Confidence**: 98%
