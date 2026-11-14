# ADR Hygiene: Fenced Codeblock Isolation for Aspirational Future Paths

## Friction Observed
- `harness.cli context lint` checks inline backticked file paths across governed Markdown files for `[path_existence]`.
- `docs/decisions/rea-size-exemptions.md` listed 9 planned future decomposition files (e.g. `src/harness/services/rea/routing.py`, `engine/pe_cli.py`, `tflite_parser.py`) as bare inline code bullets, triggering 9 persistent `[path_existence]` failures.

## Mandatory Invariant
- Wrap aspirational/future decomposition file layouts in fenced ` ```text ` blocks and avoid bare backticked filenames for non-existent example artifacts so `harness.cli context lint` stays clean (`exit_code=0`).
