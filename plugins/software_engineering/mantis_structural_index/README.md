# Mantis Structural Index Plugin (`plugin.mantis_structural_index`)

## Overview
`plugin.mantis_structural_index` implements Google Mantis's content-addressed semantic-unit indexing system. It parses source files into AST representations, computes stable cryptographic hashes of code units (functions, classes, methods), and maps call cross-references into an indexed SQLite database for fast, token-bounded queries.

## Service Key
- **Key**: `service.mantis_structural_index`
- **Type**: `ServiceKey[MantisStructuralIndexService]`

## Exported Tools
- `mantis_build_structural_index`: Crawl and parse codebase AST into content-addressed semantic units.
- `mantis_query_symbol`: Look up symbol definitions, caller references, signatures, and AST hashes without loading full source files.

## Architectural Deepening (Rule 20)
Complements Brain Harness's `RepoMapService` by providing offline, content-addressed SQLite AST caching for instant symbol cross-referencing during ReAct agent step execution.
