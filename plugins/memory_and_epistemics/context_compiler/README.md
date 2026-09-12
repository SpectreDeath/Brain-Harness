# domain.context_compiler (v1.0.0)

AST-based 3-tier token-efficient context compilation, skeletonization, and reachability resolver for agent workflows

---

## Overview & Metadata

- **Plugin Directory**: `plugins/memory_and_epistemics/context_compiler`
- **Isolation Mode**: `subprocess`
- **Services Provided**: None
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `compile_context` | `(repo_root, target_file, max_hops)` | Compile a 3-tier token-efficient context window (Full source, Skeletonized dependencies, Excluded files) with prompt string and diagnostics |
| `skeletonize_code` | `(source_code)` | Strip function and method bodies from Python source, preserving signatures and docstrings |
| `resolve_reachability` | `(repo_root, target_file, max_hops)` | Perform multi-hop AST symbol and import reachability analysis from a target file |
| `estimate_token_reduction` | `(repo_root, target_file, max_hops)` | Calculate potential token savings of compiled 3-tier context versus a naive repository dump |

---

## Key Modules & AST Symbols

### Module [`compiler_core.py`](compiler_core.py)

Core AST skeletonizing, symbol reachability analysis, and 3-tier context compilation engine.

#### Classes

- `class CodeSkeletonizer`
  Strips function and method bodies, leaving only signatures and docstrings.
  - `def __init__() -> None`
  - `def visit_FunctionDef(node) -> ast.FunctionDef`
  - `def visit_AsyncFunctionDef(node) -> ast.AsyncFunctionDef`
  - `def visit_Module(node) -> ast.Module`
- `class SkeletonizerRegistry`
  Polyglot structural skeletonizer registry handling Python, JSON, Markdown, and text.
  - `def skeletonize_json(content, max_items) -> tuple[str, int]`
  - `def skeletonize_markdown(content) -> tuple[str, int]`
  - `def skeletonize(cls, path, content) -> tuple[str, int]`
- `class ModuleIndex`
  Maps every .py file in a repository to its dotted module path, and back.
  - `def build(cls, root) -> ModuleIndex`
  - `def resolve_import(module_name) -> Path | None`
- `class FileSymbols`
- `class ReachabilityResult`
  - `def to_dict() -> dict[str, Any]`
- `class SymbolResolver`
  Builds an approximate reachability graph outward from a target file.
  - `def __init__(repo_root, max_hops) -> None`
  - `def resolve(target_file) -> ReachabilityResult`
- `class TierEntry`
  - `def to_dict() -> dict[str, Any]`
- `class CompiledContext`
  - `def to_prompt_string() -> str`
  - `def reduction_pct() -> float`
  - `def summary() -> str`
  - `def to_dict() -> dict[str, Any]`
- `class ContextCompiler`
  Orchestrates 3-tier AST context compilation for agent workflows.
  - `def __init__(repo_root, max_hops) -> None`
  - `def compile(target_file) -> CompiledContext`


#### Functions

- `def estimate_tokens(text) -> int`
  - Estimate token count with 4 chars/token heuristic.
- `def skeletonize_source(source) -> tuple[str, int]`
  - Reduce Python source code to its structural interface skeleton.
- `def extract_symbols(source) -> FileSymbols`


### Module [`main.py`](main.py)

Main entrypoint and typed tool registrations for Context Compiler plugin.

#### Classes

- `class ContextCompilerService`
  Service provider for 3-tier AST context compilation.
  - `def compile(repo_root, target_file, max_hops) -> dict[str, Any]`
  - `def skeletonize(source_code) -> dict[str, Any]`
  - `def resolve(repo_root, target_file, max_hops) -> dict[str, Any]`
  - `def estimate_reduction(repo_root, target_file, max_hops) -> dict[str, Any]`


#### Functions

- `def compile_context(repo_root, target_file, max_hops) -> dict[str, Any]`
  - Compile a 3-tier token-efficient context window for a target file in a repository.
- `def skeletonize_code(source_code) -> dict[str, Any]`
  - Strip function and method bodies from Python source, preserving signatures and docstrings.
- `def resolve_reachability(repo_root, target_file, max_hops) -> dict[str, Any]`
  - Perform multi-hop AST symbol and import reachability analysis from a target file.
- `def estimate_token_reduction(repo_root, target_file, max_hops) -> dict[str, Any]`
  - Calculate potential token savings of compiled 3-tier context versus a naive repository dump.



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
