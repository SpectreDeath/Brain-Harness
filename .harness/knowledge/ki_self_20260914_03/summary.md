# Scratch Runner UTF-8 Stream Codec & SysPath Precedence Protocol

## Executive Summary
This Knowledge Item establishes the strict operational execution pattern for scratch runner scripts (`<appDataDir>\brain\<cid>\scratch\*.py`), addressing the three most prevalent execution frictions observed in Windows multi-agent development.

## Operational Standards
1. **UTF-8 Stream Codec Entrypoint (Rule 23 & Rule 50)**:
   - On Windows environments, `sys.stdout` and `sys.stderr` default to legacy `cp1252`.
   - Every scratch runner script must execute this invariant at line 1:
     ```python
     import sys
     if hasattr(sys.stdout, "reconfigure"):
         sys.stdout.reconfigure(encoding="utf-8")
     if hasattr(sys.stderr, "reconfigure"):
         sys.stderr.reconfigure(encoding="utf-8")
     ```
2. **Workspace Root SysPath Precedence (Rule 50)**:
   - Scripts executing from brain directories resolve `__file__` to the brain scratch folder, causing `import harness` and `import plugins` to fail.
   - Every scratch script inspecting repository code must inject:
     ```python
     from pathlib import Path
     workspace_root = Path(r"d:\GitHub\projects\Brain Harness") # or dynamic resolution
     sys.path.insert(0, str(workspace_root / "src"))
     sys.path.insert(0, str(workspace_root))
     ```
3. **F-String Template Escaping Invariant (Rule 51)**:
   - When generating standalone HTML visual briefs in `%TEMP%`, CSS `<style>` blocks contain single curly braces `{ background: ... }`.
   - In Python f-strings, all CSS rules and literal curly braces must be doubled (`{{ ... }}`) or isolated into non-formatted raw multiline string constants.

## Verifiable Isnad Lineage
- **Grounding Trajectories**: `5c4a8109` (cp1252 crash & plugin import fix), `b1c6bfd4` (Unicode character '│' crash & harness module resolution), `2664f7a5` (f-string CSS escaping in triad_pipeline.py).
- **Governing Invariants**: `AGENTS.md` Rule 23, Rule 29, Rule 46, Rule 50, Rule 51.
