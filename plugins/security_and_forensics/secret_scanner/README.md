# plugin.secret_scanner (v1.0.0)

Pre-ingestion and on-demand credential & API key scanner with Shannon entropy analysis

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/security_and_forensics/secret_scanner` |
| Category | `security_and_forensics` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `scan_text` | `(text)` | Scan raw text or code string for potential credentials, tokens, and private keys |
| `scan_file` | `(file_path)` | Scan a specific file on disk for leaked credentials and keys |
| `scan_directory` | `(dir_path, max_depth)` | Recursively scan a directory tree for leaked credentials and secret tokens |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Secret Scanner & Credential Leak Detection Plugin for Brain Harness.

Performs static regex pattern matching and Shannon entropy analysis to detect
hardcoded API keys, private keys, access tokens, and credentials in source code.

#### Classes

- `class SecretScannerService` — Service facade for credential & secret scanning.
  - `def scan_text(text) -> dict[str, Any]`
  - `def scan_file(file_path) -> dict[str, Any]`
  - `def scan_directory(dir_path, max_depth) -> dict[str, Any]`
- `class SecretScannerPlugin` — Plugin providing secret scanning capabilities to the Harness kernel.
  - `def name() -> str`
  - `def version() -> str`
  - `def description() -> str`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`


#### Functions

- `def scan_text(text) -> dict[str, Any]` — Scan raw text or code string for potential credentials, tokens, and private keys.
- `def scan_file(file_path) -> dict[str, Any]` — Scan a specific file on disk for credentials.
- `def scan_directory(dir_path, max_depth) -> dict[str, Any]` — Recursively scan a directory for leaked credentials.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.security_and_forensics.secret_scanner.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
