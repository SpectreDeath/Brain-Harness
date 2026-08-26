# Vibe Scanner Plugin (`plugin.vibe_scanner`)

Static AST security analysis plugin designed to detect vulnerabilities and anti-patterns commonly introduced in AI-generated / vibe-coded Python applications.

## Key Capabilities

- **Zero External Dependencies**: Operates entirely on Python's built-in `ast` module and standard library.
- **Context-Aware Taint Analysis**: Analyzes variable proximity and call sites without high false-positive rates.
- **Actionable Remediation**: Every vulnerability finding includes exact file coordinates, surrounding code context lines, and an actionable fix hint.
- **SARIF & JSON Export**: Native export for GitHub Advanced Security and CI/CD pipelines.

## 7 Core Detectors

| Detector | What It Catches | Default Severity |
|---|---|---|
| `SQLInjectionDetector` | Unparameterized SQL queries (`f"SELECT...{param}"`, `%`, `.format()`) | `CRITICAL` |
| `UnsafeFileAccessDetector` | Path traversal vulnerabilities (`Path / user_input` without `.resolve().relative_to()`) | `CRITICAL` |
| `HardcodedSecretDetector` | Hardcoded API keys (OpenAI, Anthropic, AWS, GitHub) & literal passwords | `CRITICAL` |
| `UnsafeDeserialiseDetector` | Insecure deserialization via `pickle.loads()` or `yaml.load()` without SafeLoader | `CRITICAL` |
| `WeakCryptoDetector` | MD5/SHA1 used in security/token contexts or pseudo-random `random()` for auth | `CRITICAL` |
| `ExceptionSwallowedDetector` | Bare `except:` clauses or `except Exception: pass` masking critical runtime failures | `HIGH` |
| `InputValidationDetector` | Unvalidated user input sources flowing into dangerous sinks | `HIGH` |

## Agent Tools

### 1. `scan_code(code: str, file_name: str = "snippet.py")`
```python
result = scan_code("""
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
""")
# Returns findings with severity CRITICAL, line number, and fix hint.
```

### 2. `scan_file(file_path: str)`
```python
result = scan_file("path/to/script.py")
```

### 3. `scan_project(dir_path: str, ignore_dirs: list[str] = None, fail_on_critical: bool = False)`
```python
result = scan_project("./src", fail_on_critical=True)
```

### 4. `compare_benchmark(vulnerable_code: str, secure_code: str)`
```python
result = compare_benchmark(vulnerable_snippet, remediated_snippet)
# Returns side-by-side finding diffs, findings eliminated, and risk reduction percentage.
```

### 5. `generate_sarif_report(dir_path: str, output_path: str)`
```python
result = generate_sarif_report("./src", "report.sarif")
```
