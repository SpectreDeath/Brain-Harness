# plugin.vibe_scanner (v1.0.0)

Static AST security scanner detecting AI-generated code vulnerabilities, secrets, SQL injection, path traversal, weak crypto, and anti-patterns

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/security_and_forensics/vibe_scanner` |
| Category | `security_and_forensics` |
| Isolation Mode | `subprocess` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `scan_code` | `(code, file_name)` | Scan in-memory Python source code string for 7 AI security vulnerability classes with line numbers and fix hints |
| `scan_file` | `(file_path)` | Scan a single Python source file on disk for AST security vulnerabilities |
| `scan_project` | `(dir_path, ignore_dirs, fail_on_critical)` | Recursively scan a project directory of Python files, skipping virtual environments and caches |
| `compare_benchmark` | `(vulnerable_code, secure_code)` | Compare vulnerable code against remediated/secure code to verify risk reduction and fix efficacy |
| `generate_sarif_report` | `(dir_path, output_path)` | Scan a project directory and export a standard SARIF v2.1.0 security report for GitHub Security integration |
| `generate_json_report` | `(dir_path, output_path)` | Scan a project directory and export a structured JSON security findings report |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Vibe Scanner plugin — AST-based AI code vulnerability detector & security auditing.

Detects common AI/vibe-coding anti-patterns and vulnerabilities:
  - SQL Injection (unparameterized f-strings, format, %)
  - Path Traversal & Unsafe File Access
  - Hardcoded API Keys, Passwords & Secrets
  - Unsafe Deserialization (pickle, yaml.load)
  - Weak Cryptography (MD5/SHA1 for auth, random() tokens)
  - Swallowed Exceptions (bare except, pass)
  - Tainted Input Validation & Flow

#### Classes

- `class VibeScannerService` — Service class for in-process or kernel lifecycle integration.
  - `def scan_code(code, file_name) -> dict[str, Any]`
  - `def scan_file(file_path) -> dict[str, Any]`
  - `def scan_project(dir_path, ignore_dirs, fail_on_critical) -> dict[str, Any]`
  - `def compare_benchmark(vulnerable_code, secure_code) -> dict[str, Any]`
  - `def generate_sarif(dir_path, output_path) -> dict[str, Any]`
  - `def generate_json(dir_path, output_path) -> dict[str, Any]`


#### Functions

- `def scan_code(code, file_name) -> dict[str, Any]` — Scan in-memory Python source code string for AI security vulnerabilities and anti-patterns.
- `def scan_file(file_path) -> dict[str, Any]` — Scan a single Python source file on disk for AST security vulnerabilities.
- `def scan_project(dir_path, ignore_dirs, fail_on_critical) -> dict[str, Any]` — Recursively scan a directory of Python files, skipping virtual environments and caches.
- `def compare_benchmark(vulnerable_code, secure_code) -> dict[str, Any]` — Compare vulnerable code against remediated/secure code to verify risk reduction.
- `def generate_sarif_report(dir_path, output_path) -> dict[str, Any]` — Scan a project directory and export a standard SARIF v2.1.0 security report.
- `def generate_json_report(dir_path, output_path) -> dict[str, Any]` — Scan a project directory and export a structured JSON security report.

### Module [scanner_core.py](scanner_core.py)

scanner.py
----------
AI Blind Spot Scanner — zero dependencies, pure Python stdlib.

Detects the seven vulnerability patterns that AI coding tools
consistently introduce but standard linters miss:

    1. InputValidator     — missing input validation before use
    2. UnsafeFileAccess   — path traversal, unchecked file ops
    3. ExceptionSwallowed — bare excepts, swallowed exceptions
    4. HardcodedSecret    — API keys, passwords, tokens in code
    5. UnsafeDeserialise  — pickle, yaml.load, marshal
    6. SQLInjection       — string-formatted queries
    7. WeakCrypto         — md5/sha1 for security, random for secrets

Pure Python 3.8+. No pip install. No API. No internet.
Run: python scanner.py /path/to/project

Full code: https://github.com/Emmimal/vibe-scanner/

#### Classes

- `class Finding` — A single vulnerability finding.
- `class ScanResult` — Full scan result for one file.
  - `def critical() -> List[Finding]`
  - `def high() -> List[Finding]`
- `class ScanReport` — Aggregated report across all files.
  - `def effective_ms() -> float` — Real scan time — from total_ms if set, else sum of individual file times.
  - `def all_findings() -> List[Finding]`
  - `def by_severity() -> Dict[str, List[Finding]]`
  - `def by_detector() -> Dict[str, List[Finding]]`
  - `def files_clean() -> int`
  - `def files_vulnerable() -> int`
- `class BaseDetector` — All detectors inherit from this.
  - `def detect(tree, source, path) -> List[Finding]`
- `class InputValidationDetector` — Detects user input used directly without validation.
  - `def detect(tree, source, path) -> List[Finding]`
- `class UnsafeFileAccessDetector` — Detects path traversal vulnerabilities and unchecked file ops.
  - `def detect(tree, source, path) -> List[Finding]`
- `class ExceptionSwallowedDetector` — Detects bare excepts and swallowed exceptions.
  - `def detect(tree, source, path) -> List[Finding]`
- `class HardcodedSecretDetector` — Detects API keys, passwords, tokens hardcoded in source.
  - `def detect(tree, source, path) -> List[Finding]`
- `class UnsafeDeserialiseDetector` — Detects pickle, yaml.load, marshal — classic AI blind spots.
  - `def detect(tree, source, path) -> List[Finding]`
- `class SQLInjectionDetector` — Detects string-formatted SQL queries.
  - `def detect(tree, source, path) -> List[Finding]`
- `class WeakCryptoDetector` — Detects MD5/SHA1 used for security, random used for secrets.
  - `def detect(tree, source, path) -> List[Finding]`


#### Functions

- `def scan_file(path) -> ScanResult` — Scan a single Python file with all detectors.
- `def scan_directory(root, ignore_dirs) -> ScanReport` — Scan all .py files in a directory recursively.
- `def print_report(report, verbose) -> None`
- `def export_json(report, output_path) -> None` — Export report as JSON for CI integration.
- `def export_sarif(report, output_path) -> None` — Export findings as SARIF 2.1.0 for GitHub code scanning.
- `def main()`


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.security_and_forensics.vibe_scanner.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `subprocess` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
