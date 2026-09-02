# Windows UTF-8 Stream Codec Isolation

## Metadata
- **KI ID**: `ki_self_20260901_02`
- **Source Target**: `d:\GitHub\projects\Brain Harness`
- **Format**: `python_cross_platform_runtime`
- **Timestamp**: `2026-09-01T17:35:00Z`
- **Status**: `VERIFIED`

## Distilled Learning
# KI: Windows UTF-8 Stream Codec Isolation

## Operational Summary
Across Windows host systems, Python's default standard output and error streams initialize with the system active code page (`cp1252` or `windows-1252`). When agent reflection scripts, CLI tree formatters, or test reporters emit Unicode arrows (`→`, `➔`), checkmarks (`✓`), or mathematical notation (`$eta$`, `$\gamma$`, `$\sum$`), unconfigured stdout streams immediately raise:
`UnicodeEncodeError: 'charmap' codec can't encode character ... character maps to <undefined>`.

To ensure complete terminal idempotency across operating systems without stripping rich visual artifacts:
1. Reconfigure standard streams at module import: `sys.stdout.reconfigure(encoding='utf-8')` and `sys.stderr.reconfigure(encoding='utf-8')`.
2. Explicitly set environment variable `PYTHONIOENCODING=utf-8` in subprocess runners and background tasks.

## Invariant Rule
All CLI entrypoints, background task runners, and reflection extractors must explicitly enforce UTF-8 stream reconfiguration at module initialization to eliminate charmap encode crashes across Windows environments.

## Primary Lineage
- **Assertion**: Python processes spawned on Windows without explicit stream reconfiguration fall back to legacy console code pages (cp1252) and crash with UnicodeEncodeError when emitting Unicode DAG symbols (→, ➔, ✓, ∑). All CLI scripts, reflection extractors, and test runners must unconditionally configure sys.stdout to UTF-8 at process entrypoints.
  - `primary_code`: `src/harness/commands/main.py#L1-L80` (Verified: True)
  - `primary_code`: `.agents/scratch/inspect_all_reflections.py#L1-L25` (Verified: True)
  - `visual_brief`: `C:/Users/spectre/AppData/Local/Temp/harness-reflection-20260901-173500.html` (Verified: True)
