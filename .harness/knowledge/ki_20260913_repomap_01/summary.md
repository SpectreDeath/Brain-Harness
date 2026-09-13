# PageRanked AST Context Prioritization & Token Budget Pruning

## Context
When coding agents operate on large codebases, providing full source files exceeds model context windows and token economics. Simple grep or file-level chunking loses architectural dependency awareness.

## Distilled Learning
Implement an AST-driven repository mapping subsystem using Tree-Sitter and PageRank graph weighting:
- Parse all workspace files with Tree-Sitter to extract symbol definitions (classes, functions, methods) and symbol references (identifiers called or instantiated).
- Form a directed bipartite multigraph where nodes are source files and edges represent symbol dependencies (File A references symbol defined in File B).
- Compute personalized PageRank scores over the graph, biased toward files currently mentioned in conversation or active edits.
- Greedily pack top-ranked symbol signatures into a compact AST map constrained by a strict token budget (e.g. 1k–4k tokens).

## Triggers & Seam Choices
- **Trigger**: Pre-LLM step execution loops (`StepExecutionEngine`), context assembly, and repo-wide query routing.
- **Seam Choice**: Integrate in `harness.services.repo_map` (Rule 9) as a deterministic context injector before prompt synthesis.
