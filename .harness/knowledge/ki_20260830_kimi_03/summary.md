# Pure-Language Tree-Sitter Bash AST Parsing for Agent Shell Security Gates

## Architectural Summary
`@moonshot-ai/tree-sitter-bash` implements a zero-native-addon, pure-TypeScript parser matching Tree-Sitter Bash 0.25.0 node specifications.

## Operational Guidelines
1. **Zero Native Addons:** Avoid C/C++ native Node/Python extensions that require pre-compiled wheels or host build tools.
2. **Deterministic Security Traversal:** Parse commands into AST nodes (`pipeline`, `command`, `subshell`, `variable_assignment`) and evaluate safety policies on every decomposed sub-command before execution.
3. **Compound Isolation:** Prevent hidden destructive commands inside subshells (`echo $(rm -rf /)`) from slipping past regex filters.
