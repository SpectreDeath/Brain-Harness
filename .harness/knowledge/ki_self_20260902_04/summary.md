# F-String Brace Collision Avoidance in HTML Brief Generators

**ID:** `ki_self_20260902_04`  
**Category:** `reporting_and_visualization`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `generate_visual_briefs.py#line-510`, `deep-repo-auditor/SKILL.md#anti-patterns`

## Executive Summary
When constructing large HTML visual briefs with embedded JSON manifests or JavaScript objects using Python f-strings, regular dictionary and set literal braces (`out = {...}`) collide with f-string escape sequences (`{{`/`}}`), producing `TypeError: unhashable type: 'dict'`. Python dictionary and data structures must be constructed outside the f-string template block.

## Architectural Invariants & Rules
1. Decouple all Python dictionary, list, and set data construction from f-string HTML template strings.
2. Write JSON manifest files using `json.dump()` separately from HTML template rendering.
3. Escape all embedded CSS/JS curly braces as `{{` and `}}` within f-string HTML templates.
