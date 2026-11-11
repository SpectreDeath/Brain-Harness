# Semantic Signatures: sign_language_detection_model.pyc (cpython_pyc)

**Knowledge Item ID:** `ki-rea-sig-sign_language_detection_model-b20e8353`  
**Evidence Record:** `ev:e9c065c6057cf116370c99d9aeb54f6aa563ef451df617d8973bf4c22c9e15f6`  
**Artifact SHA-256:** `326971804c54529763baea43738604dd76252285f213a0967f4e1dff4174e3c4`  
**Detected Kind:** `cpython_pyc`  
**Provider:** `plugin.rea_managed_runtime`  

## Facet Availability Audit

| Facet | State | Availability Notes |
|---|---|---|
| `pyc_code` | `AVAILABLE` | `Observed` |

## Extracted Semantic Signatures (7 total)

| Signature Kind | Identifier / Symbol | Structural Metadata |
|---|---|---|
| `pyc_code_object` | `<module>` | `{"cpython_version": "3.13", "instruction_count": 23}` |
| `pyc_import` | `tensorflow` | `{"opcode": "IMPORT_NAME"}` |
| `pyc_import` | `sign_language_detection.args` | `{"opcode": "IMPORT_NAME"}` |
| `pyc_import` | `FLAGS` | `{"opcode": "IMPORT_FROM"}` |
| `pyc_function` | `input_size` | `{"cpython_version": "3.13"}` |
| `pyc_function` | `get_model` | `{"cpython_version": "3.13"}` |
| `pyc_function` | `build_model` | `{"cpython_version": "3.13"}` |

## Isnad Lineage Chain
- Grounded in empirical observation `ev:e9c065c6057cf116370c99d9aeb54f6aa563ef451df617d8973bf4c22c9e15f6` produced by `plugin.rea_managed_runtime`.
- **Provenance & Reproducibility Note (2026-11-11)**: The analyzed artifact `sign_language_detection_model.pyc` is an Antigravity external scratch file (`C:\Users\spectre\.gemini\antigravity\brain\fdc15323-dd5c-4976-8b10-5fd4cf21e2a0\scratch\sign_language_detection_model.pyc`), generated during dynamic session execution and NOT tracked as an in-repo file. It is not independently re-verifiable from repository sources alone.
- All unobserved facets strictly quarantined as `UNKNOWN` rather than conflated with zero.
