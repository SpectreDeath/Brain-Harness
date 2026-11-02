# Decoupled Multi-Editor TextMate Syntax Grammar & Tokenization Architecture

## Context & Theoretical Grounding
Syntax highlighting is often tightly coupled to IDE language servers, resulting in heavy cold-start delays and lack of portability. `vscode-R-syntax` decouples grammatical tokenization from semantic indexing.

## Distilled Mental Models & Heuristics
1. **Declarative Grammar in YAML**:
   - Source grammars are authored in human-readable YAML (`r.yaml`, `rmd.yaml`) with modular regex repositories (`#accessor`, `#constants`, `#operators`, `#keywords`, `#function-declarations`).
2. **Multi-Editor Transpilation**:
   - A single build script (`build.js`) compiles YAML definitions into VS Code TextMate JSON syntaxes and Sublime Text `.sublime-syntax` files, guaranteeing token parity across editors.
3. **Engine-Agnostic Lexical Decoupling**:
   - Decoupled grammar allows developers to switch between disparate language servers (e.g. `languageserver`, Posit's `ark`, Posit's `air`) without losing syntax coloring or experiencing editor UI stalls.

## Anti-Pattern Defenses
- **Monolithic LSP-Bound Syntax**: Restricting syntax highlighting to semantic tokens emitted by a running language server, leaving files uncolored until the background server boots.
- **Manual Duplicate Syntax Maintenance**: Maintaining separate regex files for VS Code and Sublime Text instead of a single compiled source of truth.
