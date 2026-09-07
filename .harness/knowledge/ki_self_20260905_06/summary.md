# Multi-Pass Cognitive String Salvage & AST Script Hygiene Inspection

**ID:** `ki_self_20260905_06`  
**Category:** `agent_tooling`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `.agents/skills/agent-skill-sdlc/scripts/validate_skill.py#L115-L180`, `AGENTS.md#Rule42`, `.agents/skills/agent-skill-sdlc/references/two-phase-validation-patterns.md`, `scratch/test_salvage_deep.py`

## Executive Summary
Model-generated structured outputs and skill code verification routinely encounter two failure modes:
1. **Parse Fragility**: LLMs outputting JSON frequently wrap output in markdown fences, include conversational preambles/postscripts, use single quotes, omit key quotes (`{status: "ok"}`), introduce trailing commas, and emit Python literal tokens (`True`, `False`, `None`). Naive single-pass regex slicing fails on these deviations, causing premature exceptions and costly LLM reprompts.
2. **False-Positive Script Hygiene**: Scanning script files with raw regexes (e.g. `re.search(r"\binput\s*\(", content)`) falsely flags docstrings, comments, or remediation guidance containing the token `input()`.

## Architectural Invariants & Heuristics
1. **Deterministic 5-Pass Cognitive Salvage Engine**:
   - **Pass 1**: Code fence and conversational preamble/postscript stripping.
   - **Pass 2**: Outermost brace/bracket slicing (`{...}` or `[...]`).
   - **Pass 3**: Python literal normalization (`True`/`False`/`None` $\rightarrow$ `true`/`false`/`null`) and quote standardization (`'key':` $\rightarrow$ `"key":`, unquoted `{key:` $\rightarrow$ `{"key":`).
   - **Pass 4**: Trailing comma elimination before closing brackets/braces (`,\s*([}\]])` $\rightarrow$ `\1`).
   - **Pass 5**: Safe AST literal fallback (`ast.literal_eval`) for raw Python dictionary syntax.
2. **AST Script Hygiene Invariant**:
   - Diagnostic script hygiene checks must inspect the Python Abstract Syntax Tree via `ast.walk()`, asserting that no executable call nodes exist (`isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'input'`).

Codified in `AGENTS.md` as Rule 42.
