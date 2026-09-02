# PowerShell UTF-16 Stream Redirection Traps & Fixes

## Metadata
- **KI ID**: `ki_self_20260901_scratch_03`
- **Source Target**: `C:\Users\spectre\.gemini\antigravity-ide\scratch`
- **Format**: `windows_powershell_stream_log`
- **Timestamp**: `2026-09-01T18:45:00Z`
- **Status**: `VERIFIED`

## Distilled Learning
# KI: PowerShell UTF-16 Stream Redirection Traps & Fixes

## Operational Summary
On Windows PowerShell (5.1 & Core), the default redirection operator (`> file.txt 2>&1`) formats output as UTF-16 Little Endian with Byte Order Mark (BOM). When downstream agents or Python scripts read these files as standard UTF-8 text, each single-byte ASCII character is parsed with an alternating null byte (`\x00`), resulting in spaced strings:
`p y t h o n   :   T r a c e b a c k ...`

This breaks regular expression matching, JSON parsing, and automated traceback extraction in agent loops.

To permanently avoid UTF-16 redirection corruption:
1. **Prefer Native Subprocess Capture**: Rely on the agent framework's standard runner / capture mechanisms rather than shell file redirection.
2. **Explicit Pipe Encoding**: If shell redirection is mandatory, pipe explicitly through `| Out-File -FilePath output.txt -Encoding utf8` or set `$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'`.

## Invariant Rule
Never rely on bare PowerShell `>` redirects for machine-parsed logs; always enforce UTF-8 streams (`| Out-File -Encoding utf8`) or native subprocess standard output piping to prevent UTF-16 LE BOM null-byte corruptions.

## Primary Lineage
- **Assertion**: PowerShell command redirection (> file.txt 2>&1) writes UTF-16 LE with BOM by default, inserting null bytes between ASCII characters (p y t h o n ...) when read by UTF-8 consumers. Autonomous agent harnesses must use native subprocess standard output captures or explicitly specify UTF-8 encoding in PowerShell pipes (| Out-File -Encoding utf8).
  - `primary_code`: `C:/Users/spectre/.gemini/antigravity-ide/scratch/test_debug_output.txt` (Verified: True)
  - `visual_brief`: `C:/Users/spectre/AppData/Local/Temp/harness-reflection-scratch-20260901-184500.html` (Verified: True)
