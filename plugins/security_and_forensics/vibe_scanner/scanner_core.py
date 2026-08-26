"""
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
"""

import ast
import os
import re
import sys
import json
import time
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

# ─────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────

@dataclass
class Finding:
    """A single vulnerability finding."""
    file: str
    line: int
    detector: str
    severity: str          # CRITICAL | HIGH | MEDIUM | LOW
    title: str
    detail: str
    code_snippet: str = ""
    fix_hint: str = ""

    def __repr__(self) -> str:
        return f"[{self.severity}] {self.detector} @ {self.file}:{self.line} — {self.title}"


@dataclass
class ScanResult:
    """Full scan result for one file."""
    path: str
    findings: List[Finding] = field(default_factory=list)
    lines_scanned: int = 0
    parse_error: bool = False
    scan_ms: float = 0.0

    @property
    def critical(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "CRITICAL"]

    @property
    def high(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "HIGH"]


@dataclass
class ScanReport:
    """Aggregated report across all files."""
    root: str
    results: List[ScanResult] = field(default_factory=list)
    total_ms: float = 0.0

    @property
    def effective_ms(self) -> float:
        """Real scan time — from total_ms if set, else sum of individual file times."""
        return self.total_ms if self.total_ms > 0 else sum(r.scan_ms for r in self.results)

    @property
    def all_findings(self) -> List[Finding]:
        return [f for r in self.results for f in r.findings]

    @property
    def by_severity(self) -> Dict[str, List[Finding]]:
        out = defaultdict(list)
        for f in self.all_findings:
            out[f.severity].append(f)
        return dict(out)

    @property
    def by_detector(self) -> Dict[str, List[Finding]]:
        out = defaultdict(list)
        for f in self.all_findings:
            out[f.detector].append(f)
        return dict(out)

    @property
    def files_clean(self) -> int:
        return sum(1 for r in self.results if not r.findings)

    @property
    def files_vulnerable(self) -> int:
        return sum(1 for r in self.results if r.findings)


# ─────────────────────────────────────────────
# Base detector
# ─────────────────────────────────────────────

class BaseDetector:
    """All detectors inherit from this."""
    NAME: str = "base"
    SEVERITY: str = "MEDIUM"

    def detect(self, tree: ast.AST, source: str, path: str) -> List[Finding]:
        raise NotImplementedError

    def _snippet(self, source: str, line: int, context: int = 1) -> str:
        lines = source.splitlines()
        start = max(0, line - context - 1)
        end = min(len(lines), line + context)
        return "\n".join(
            f"{'→' if i == line - 1 else ' '} {i+1:4}  {lines[i]}"
            for i in range(start, end)
        )

    def _finding(
        self,
        path: str,
        line: int,
        title: str,
        detail: str,
        source: str,
        severity: str = None,
        fix_hint: str = "",
    ) -> Finding:
        return Finding(
            file=path,
            line=line,
            detector=self.NAME,
            severity=severity or self.SEVERITY,
            title=title,
            detail=detail,
            code_snippet=self._snippet(source, line),
            fix_hint=fix_hint,
        )


# ─────────────────────────────────────────────
# Detector 1: Input Validation
# ─────────────────────────────────────────────

class InputValidationDetector(BaseDetector):
    """
    Detects user input used directly without validation.
    AI tools frequently skip length checks, type checks,
    and sanitisation — especially in Flask/FastAPI routes.
    """
    NAME = "InputValidation"
    SEVERITY = "HIGH"

    # Sources of untrusted input
    INPUT_SOURCES = {
        "request.json", "request.form", "request.args",
        "request.data", "request.get_json",
        "sys.argv", "input", "os.environ.get",
    }

    # Sinks that are dangerous without validation
    DANGEROUS_SINKS = {
        "open", "exec", "eval", "subprocess.run",
        "subprocess.call", "os.system", "os.popen",
        "cursor.execute", "conn.execute", "db.execute",
    }

    def detect(self, tree: ast.AST, source: str, path: str) -> List[Finding]:
        findings: List[Finding] = []

        # Track variables assigned from input sources
        input_vars: Dict[str, int] = {}  # var_name → line

        for node in ast.walk(tree):
            # Assignment: x = request.json.get("field")
            if isinstance(node, ast.Assign):
                if self._is_input_source(node.value):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            input_vars[target.id] = node.lineno

            # Direct call with input variable as argument
            if isinstance(node, ast.Call):
                func_name = self._func_name(node.func)
                if func_name in self.DANGEROUS_SINKS:
                    for arg in node.args:
                        if isinstance(arg, ast.Name) and arg.id in input_vars:
                            findings.append(self._finding(
                                path=path,
                                line=node.lineno,
                                title="Unvalidated input passed to dangerous sink",
                                detail=(
                                    f"Variable '{arg.id}' from user input "
                                    f"(line {input_vars[arg.id]}) passed directly "
                                    f"to '{func_name}' without validation."
                                ),
                                source=source,
                                fix_hint=(
                                    f"Validate '{arg.id}' before use: "
                                    f"check type, length, and allowed values."
                                ),
                            ))

        # Pattern: dict subscript used directly in sink (request.json["key"])
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._func_name(node.func)
                if func_name in self.DANGEROUS_SINKS:
                    for arg in node.args:
                        if self._is_input_source(arg):
                            findings.append(self._finding(
                                path=path,
                                line=node.lineno,
                                title="Raw user input passed to dangerous sink",
                                detail=(
                                    f"User input passed directly to '{func_name}' "
                                    f"with no intermediate validation."
                                ),
                                source=source,
                                fix_hint="Always validate and sanitise user input before passing to system calls.",
                            ))

        return findings

    def _is_input_source(self, node: ast.AST) -> bool:
        src = ast.unparse(node) if hasattr(ast, 'unparse') else ""
        return any(s in src for s in self.INPUT_SOURCES)

    def _func_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._func_name(node.value)}.{node.attr}"
        return ""


# ─────────────────────────────────────────────
# Detector 2: Unsafe File Access
# ─────────────────────────────────────────────

class UnsafeFileAccessDetector(BaseDetector):
    """
    Detects path traversal vulnerabilities and unchecked file ops.
    AI tools almost never add path.resolve() + .relative_to() checks.
    The Lovable breach and the rglob() incident both trace here.
    """
    NAME = "UnsafeFileAccess"
    SEVERITY = "CRITICAL"

    # Patterns that suggest user-controlled path input
    PATH_INPUT_PATTERNS = [
        r'request\.(json|form|args)',
        r'sys\.argv\[',
        r'\binput\s*\(',
        r'os\.environ\.get\s*\(',
        r'data\[[\'"]\w*[Pp]ath',
        r'data\[[\'"]\w*[Ff]ile',
        r'data\[[\'"]\w*[Nn]ame',
        r'params\[',
        r'query\[',
    ]

    # File operations that are dangerous with untrusted paths
    FILE_OPS = [
        r'\bopen\s*\(',
        r'Path\s*\(',
        r'pathlib\.Path\s*\(',
        r'os\.path\.(join|exists|isfile)',
        r'shutil\.(copy|move|rmtree)',
        r'os\.(remove|unlink|rename)',
        r'\.read_text\s*\(',
        r'\.write_text\s*\(',
        r'\.read_bytes\s*\(',
    ]

    # Safety patterns — if present nearby, it's likely safe
    SAFETY_PATTERNS = [
        r'\.resolve\(\)',
        r'\.relative_to\(',
        r'os\.path\.abspath',
        r'os\.path\.realpath',
        r'\.startswith\(',
        r'in ALLOWED_',
        r'allowlist',
        r'whitelist',
        r'secure_filename',
        r'safe_path\(',        # custom safe path helpers
        r'sanitize_path\(',
        r'validate_path\(',
        r'check_path\(',
    ]

    def detect(self, tree: ast.AST, source: str, path: str) -> List[Finding]:
        findings: List[Finding] = []
        lines = source.splitlines()

        # Track lines that contain user input sources
        input_lines: List[int] = []
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                continue
            if any(re.search(p, line) for p in self.PATH_INPUT_PATTERNS):
                input_lines.append(i)

        # For each line with a file op, check if input appeared nearby (within 10 lines)
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                continue

            has_file_op = any(re.search(p, line) for p in self.FILE_OPS)
            if not has_file_op:
                continue

            # Check if any input source appears within 10 lines before this line
            nearby_input = any(
                0 < (i - inp_line) <= 10
                for inp_line in input_lines
            ) or any(re.search(p, line) for p in self.PATH_INPUT_PATTERNS)

            if not nearby_input:
                continue

            # Check surrounding context for safety patterns
            context_start = max(0, i - 15)
            context_end = min(len(lines), i + 5)
            context = "\n".join(lines[context_start:context_end])

            has_safety = any(
                re.search(p, context) for p in self.SAFETY_PATTERNS
            )

            if not has_safety:
                findings.append(self._finding(
                    path=path,
                    line=i,
                    title="Unsafe file access with user-controlled path",
                    detail=(
                        "File operation uses a path derived from user input "
                        "with no path traversal protection. "
                        "An attacker can use '../../../etc/passwd' to escape the sandbox."
                    ),
                    source=source,
                    fix_hint=(
                        "Use: safe = Path(user_path).resolve()\n"
                        "Then: safe.relative_to(BASE_DIR)  # raises ValueError if outside"
                    ),
                ))

        # Detect rglob() with no depth limit — the rglob incident
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and
                        node.func.attr == "rglob"):
                    # Check if there's no max_depth or depth limit nearby
                    findings.append(self._finding(
                        path=path,
                        line=node.lineno,
                        title="Unbounded rglob() — performance and path risk",
                        detail=(
                            "rglob() scans recursively with no depth limit. "
                            "On large directories this hangs indefinitely. "
                            "AI tools use rglob() by default — it should be opt-in."
                        ),
                        source=source,
                        severity="MEDIUM",
                        fix_hint=(
                            "Replace rglob() with glob() for shallow search. "
                            "Add recursive=False as default, require explicit opt-in."
                        ),
                    ))

        return findings


# ─────────────────────────────────────────────
# Detector 3: Silent Failures
# ─────────────────────────────────────────────

class ExceptionSwallowedDetector(BaseDetector):
    """
    Detects bare excepts and swallowed exceptions.
    AI tools generate try/except blocks that catch everything
    and do nothing — masking real failures silently in production.
    """
    NAME = "ExceptionSwallowed"
    SEVERITY = "HIGH"

    def detect(self, tree: ast.AST, source: str, path: str) -> List[Finding]:
        findings: List[Finding] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue

            # Bare except: (catches everything including KeyboardInterrupt)
            if node.type is None:
                findings.append(self._finding(
                    path=path,
                    line=node.lineno,
                    title="Bare except catches everything silently",
                    detail=(
                        "A bare 'except:' catches ALL exceptions including "
                        "KeyboardInterrupt and SystemExit. "
                        "AI tools generate this pattern when uncertain what might fail."
                    ),
                    source=source,
                    severity="HIGH",
                    fix_hint="Replace with 'except Exception as e:' and log or re-raise.",
                ))
                continue

            # except Exception with empty body or only pass/...
            body = node.body
            is_silent = all(
                isinstance(stmt, (ast.Pass, ast.Expr)) and (
                    isinstance(stmt, ast.Pass) or
                    (isinstance(stmt.value, ast.Constant) and
                     stmt.value.value is ...)
                )
                for stmt in body
            )

            if is_silent:
                exc_name = ast.unparse(node.type) if hasattr(ast, 'unparse') else "Exception"
                findings.append(self._finding(
                    path=path,
                    line=node.lineno,
                    title=f"Exception '{exc_name}' swallowed silently",
                    detail=(
                        f"Caught '{exc_name}' but the handler is empty (pass/...). "
                        "The failure disappears. Production systems fail silently "
                        "for minutes or hours before anyone notices."
                    ),
                    source=source,
                    severity="HIGH",
                    fix_hint="At minimum: log the exception. Better: re-raise or return an error.",
                ))
                continue

            # except with only a comment or logger.debug (too quiet)
            has_only_debug = all(
                isinstance(stmt, ast.Expr) and
                isinstance(stmt.value, ast.Call) and
                isinstance(stmt.value.func, ast.Attribute) and
                stmt.value.func.attr in ("debug",)
                for stmt in body
                if not isinstance(stmt, ast.Pass)
            )

            if has_only_debug and len(body) <= 2:
                findings.append(self._finding(
                    path=path,
                    line=node.lineno,
                    title="Exception logged at DEBUG level only — invisible in production",
                    detail=(
                        "Exception is caught and logged at DEBUG level. "
                        "Production logging is typically INFO or WARNING — "
                        "this failure will be invisible."
                    ),
                    source=source,
                    severity="MEDIUM",
                    fix_hint="Use logger.warning() or logger.error() for exception handlers.",
                ))

        return findings


# ─────────────────────────────────────────────
# Detector 4: Hardcoded Secrets
# ─────────────────────────────────────────────

class HardcodedSecretDetector(BaseDetector):
    """
    Detects API keys, passwords, tokens hardcoded in source.
    AI tools frequently generate working examples with real-looking
    secrets — and developers ship them without noticing.
    Secret leakage is 6.4% higher in AI-assisted repos.
    """
    NAME = "HardcodedSecret"
    SEVERITY = "CRITICAL"

    # Variable name patterns that suggest secrets
    SECRET_VAR_PATTERNS = [
        r'\b(api_key|apikey|api_token|access_token|secret_key|secret)\s*=',
        r'\b(password|passwd|pwd)\s*=',
        r'\b(private_key|signing_key|auth_token)\s*=',
        r'\b(aws_secret|stripe_key|openai_key|anthropic_key)\s*=',
        r'\b(database_password|db_password|db_pass)\s*=',
        r'\b(jwt_secret|session_secret|cookie_secret)\s*=',
    ]

    # Value patterns that look like real secrets (not env var lookups)
    REAL_SECRET_PATTERNS = [
        r'=\s*["\'][a-zA-Z0-9+/]{20,}["\']',   # long base64-ish strings
        r'=\s*["\']sk-[a-zA-Z0-9]{20,}["\']',   # OpenAI-style keys
        r'=\s*["\']pk_[a-zA-Z0-9]{20,}["\']',   # Stripe-style keys
        r'=\s*["\']ghp_[a-zA-Z0-9]{36}["\']',   # GitHub tokens
        r'=\s*["\'][A-Z0-9]{20,}["\']',          # AWS-style keys
    ]

    # Safe patterns (using env vars or config)
    SAFE_PATTERNS = [
        r'os\.environ',
        r'os\.getenv',
        r'getenv',
        r'environ\[',
        r'config\[',
        r'settings\.',
        r'None',
        r'""',
        r"''",
        r'your[_-]',
        r'xxx',
        r'placeholder',
        r'example',
        r'changeme',
        r'<',
        r'\$\{',
    ]

    def detect(self, tree: ast.AST, source: str, path: str) -> List[Finding]:
        findings: List[Finding] = []
        lines = source.splitlines()

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            # Skip function calls — secret vars are assignments, not call arguments.
            # This prevents cursor.execute(f"...{password}...") being misclassified
            # as a hardcoded secret when it is already caught by SQLInjectionDetector.
            if re.search(r'\.\s*execute\s*\(', line):
                continue

            line_lower = line.lower()

            # Check for secret variable names
            has_secret_var = any(
                re.search(p, line_lower) for p in self.SECRET_VAR_PATTERNS
            )
            if not has_secret_var:
                continue

            # Check if value looks like a real secret (not env var)
            has_safe = any(re.search(p, line, re.IGNORECASE) for p in self.SAFE_PATTERNS)
            if has_safe:
                continue

            # Check if value is a non-empty string literal
            has_real_value = (
                re.search(r'=\s*["\'][^"\']{8,}["\']', line) or
                any(re.search(p, line) for p in self.REAL_SECRET_PATTERNS)
            )

            if has_real_value:
                findings.append(self._finding(
                    path=path,
                    line=i,
                    title="Hardcoded secret in source code",
                    detail=(
                        "A credential or secret appears to be hardcoded as a "
                        "string literal. AI tools generate working code with "
                        "placeholder secrets that developers forget to replace."
                    ),
                    source=source,
                    fix_hint=(
                        "Use environment variables: \n"
                        "  secret = os.environ.get('MY_SECRET')\n"
                        "Never commit secrets to version control."
                    ),
                ))

        return findings


# ─────────────────────────────────────────────
# Detector 5: Unsafe Deserialisation
# ─────────────────────────────────────────────

class UnsafeDeserialiseDetector(BaseDetector):
    """
    Detects pickle, yaml.load, marshal — classic AI blind spots.
    The multiplayer snake game used pickle for network data.
    AI tools use pickle because it's convenient and common in training data.
    """
    NAME = "UnsafeDeserialise"
    SEVERITY = "CRITICAL"

    UNSAFE_CALLS = {
        "pickle.loads": (
            "pickle.loads() executes arbitrary Python code. "
            "Any attacker who can control the input can achieve RCE."
        ),
        "pickle.load": (
            "pickle.load() from an untrusted file or socket enables RCE. "
            "AI tools use pickle for convenience — it is never safe with external data."
        ),
        "marshal.loads": (
            "marshal.loads() is as dangerous as pickle — arbitrary code execution."
        ),
        "yaml.load": (
            "yaml.load() without Loader=yaml.SafeLoader executes arbitrary Python. "
            "AI tools almost never add the SafeLoader argument."
        ),
        "__reduce__": (
            "__reduce__ defined on a class — enables arbitrary code execution "
            "when the object is unpickled."
        ),
    }

    def detect(self, tree: ast.AST, source: str, path: str) -> List[Finding]:
        findings: List[Finding] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            call_str = ast.unparse(node.func) if hasattr(ast, 'unparse') else ""

            for pattern, detail in self.UNSAFE_CALLS.items():
                if pattern in call_str:
                    # yaml.load — check if SafeLoader is present
                    if pattern == "yaml.load":
                        args_str = ast.unparse(node) if hasattr(ast, 'unparse') else ""
                        if "SafeLoader" in args_str or "safe_load" in args_str:
                            continue

                    findings.append(self._finding(
                        path=path,
                        line=node.lineno,
                        title=f"Unsafe deserialisation: {pattern}()",
                        detail=detail,
                        source=source,
                        fix_hint=(
                            "For pickle: use JSON instead.\n"
                            "For yaml: use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader).\n"
                            "For marshal: use json or struct instead."
                        ),
                    ))
                    break

        return findings


# ─────────────────────────────────────────────
# Detector 6: SQL Injection
# ─────────────────────────────────────────────

class SQLInjectionDetector(BaseDetector):
    """
    Detects string-formatted SQL queries.
    AI tools generate f-string and %-formatted queries
    because that pattern dominates their training data.
    """
    NAME = "SQLInjection"
    SEVERITY = "CRITICAL"

    # SQL keywords that suggest a query
    SQL_KEYWORDS = [
        "SELECT", "INSERT", "UPDATE", "DELETE",
        "DROP", "CREATE", "ALTER", "EXEC",
        "select", "insert", "update", "delete",
    ]

    # Formatting patterns that indicate injection risk
    INJECTION_PATTERNS = [
        r'f["\'].*SELECT.*\{',
        r'f["\'].*INSERT.*\{',
        r'f["\'].*UPDATE.*\{',
        r'f["\'].*DELETE.*\{',
        r'".*SELECT.*"\s*%\s*',
        r'".*INSERT.*"\s*%\s*',
        r'".*UPDATE.*"\s*%\s*',
        r'".*DELETE.*"\s*%\s*',
        r'\.format\(.*\).*(?:SELECT|INSERT|UPDATE|DELETE)',
        r'(?:SELECT|INSERT|UPDATE|DELETE).*\.format\(',
        r'(?:SELECT|INSERT|UPDATE|DELETE).*f["\']',
        r'query\s*[+=]\s*.*\+.*(?:user|input|param|data|name|id)',
        r'sql\s*[+=]\s*.*\+.*(?:user|input|param|data|name|id)',
    ]

    def detect(self, tree: ast.AST, source: str, path: str) -> List[Finding]:
        findings: List[Finding] = []
        lines = source.splitlines()

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            for pattern in self.INJECTION_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(self._finding(
                        path=path,
                        line=i,
                        title="SQL injection via string formatting",
                        detail=(
                            "SQL query constructed using string formatting (f-string, %, .format). "
                            "AI tools generate this pattern because it's common in training data. "
                            "Any user-controlled value in the query enables SQL injection."
                        ),
                        source=source,
                        fix_hint=(
                            "Use parameterised queries:\n"
                            "  cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))\n"
                            "Never concatenate or format user input into SQL."
                        ),
                    ))
                    break

        return findings


# ─────────────────────────────────────────────
# Detector 7: Weak Cryptography
# ─────────────────────────────────────────────

class WeakCryptoDetector(BaseDetector):
    """
    Detects MD5/SHA1 used for security, random used for secrets.
    AI tools use these because they are common and simple —
    not because they are appropriate for security contexts.
    """
    NAME = "WeakCrypto"
    SEVERITY = "HIGH"

    # Weak hash functions when used for security (not checksums)
    WEAK_HASH_PATTERNS = [
        r'hashlib\.md5\s*\(',
        r'hashlib\.sha1\s*\(',
        r'md5\s*\(',
        r'sha1\s*\(',
    ]

    # Insecure random for security purposes
    INSECURE_RANDOM_PATTERNS = [
        r'random\.random\s*\(',
        r'random\.randint\s*\(',
        r'random\.choice\s*\(',
        r'random\.shuffle\s*\(',
    ]

    # Context words that suggest security use
    SECURITY_CONTEXT = [
        'password', 'token', 'secret', 'key', 'salt',
        'auth', 'session', 'csrf', 'nonce', 'otp',
        'hash', 'sign', 'verify', 'credential',
    ]

    def detect(self, tree: ast.AST, source: str, path: str) -> List[Finding]:
        findings: List[Finding] = []
        lines = source.splitlines()

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            # Context window around the line
            ctx_start = max(0, i - 4)
            ctx_end = min(len(lines), i + 2)
            context = " ".join(lines[ctx_start:ctx_end]).lower()

            in_security_context = any(w in context for w in self.SECURITY_CONTEXT)

            has_weak_hash = any(re.search(p, line) for p in self.WEAK_HASH_PATTERNS)
            has_insecure_random = in_security_context and any(
                re.search(p, line) for p in self.INSECURE_RANDOM_PATTERNS
            )

            if has_weak_hash and has_insecure_random:
                # Both issues on same line — emit a single merged finding
                findings.append(self._finding(
                    path=path,
                    line=i,
                    title="Weak crypto: MD5 + insecure random combined",
                    detail=(
                        "Two cryptographic weaknesses on the same line: "
                        "(1) MD5/SHA1 are cryptographically broken and must not be used for "
                        "passwords, tokens, or signatures. "
                        "(2) Python's random module is not cryptographically secure — "
                        "tokens generated this way are predictable and brute-forceable."
                    ),
                    source=source,
                    severity="CRITICAL",
                    fix_hint=(
                        "Replace both:\n"
                        "  import secrets, hashlib\n"
                        "  token = secrets.token_urlsafe(32)          # secure token\n"
                        "  h = hashlib.sha256(password.encode()).hexdigest()  # secure hash\n"
                        "For passwords use bcrypt, argon2, or scrypt."
                    ),
                ))
                continue  # don't also emit the two individual findings

            # Weak hash only
            if has_weak_hash:
                findings.append(self._finding(
                    path=path,
                    line=i,
                    title="Weak hash function for security use",
                    detail=(
                        "MD5 and SHA1 are cryptographically broken. "
                        "AI tools use them because they are common in training data. "
                        "They should never be used for passwords, signatures, or tokens."
                    ),
                    source=source,
                    severity="HIGH" if in_security_context else "MEDIUM",
                    fix_hint=(
                        "For passwords: use bcrypt, argon2, or scrypt.\n"
                        "For tokens/signatures: use hashlib.sha256() or SHA3-256.\n"
                        "For checksums only: MD5/SHA1 are acceptable."
                    ),
                ))

            # Insecure random only
            if has_insecure_random:
                findings.append(self._finding(
                    path=path,
                    line=i,
                    title="Insecure random used in security context",
                    detail=(
                        "Python's random module is not cryptographically secure. "
                        "AI tools use it for convenience. "
                        "Tokens, session IDs, and salts generated this way are predictable."
                    ),
                    source=source,
                    severity="CRITICAL",
                    fix_hint=(
                        "Use secrets module instead:\n"
                        "  import secrets\n"
                        "  token = secrets.token_urlsafe(32)\n"
                        "  salt = secrets.token_bytes(16)"
                    ),
                ))

        return findings


# ─────────────────────────────────────────────
# File scanner
# ─────────────────────────────────────────────

DETECTORS = [
    InputValidationDetector(),
    UnsafeFileAccessDetector(),
    ExceptionSwallowedDetector(),
    HardcodedSecretDetector(),
    UnsafeDeserialiseDetector(),
    SQLInjectionDetector(),
    WeakCryptoDetector(),
]


def scan_file(path: str) -> ScanResult:
    """Scan a single Python file with all detectors."""
    result = ScanResult(path=path)
    t0 = time.perf_counter()

    try:
        source = Path(path).read_text(encoding="utf-8", errors="replace")
        result.lines_scanned = source.count("\n") + 1
    except Exception as e:
        result.parse_error = True
        result.scan_ms = (time.perf_counter() - t0) * 1000
        return result

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        result.parse_error = True
        result.scan_ms = (time.perf_counter() - t0) * 1000
        return result

    for detector in DETECTORS:
        try:
            findings = detector.detect(tree, source, path)
            result.findings.extend(findings)
        except Exception:
            pass  # never let a detector crash the scan

    result.scan_ms = (time.perf_counter() - t0) * 1000
    return result


def scan_directory(root: str, ignore_dirs: set = None) -> ScanReport:
    """Scan all .py files in a directory recursively."""
    ignore_dirs = ignore_dirs or {
        ".git", "__pycache__", ".venv", "venv", "env",
        "node_modules", ".mypy_cache", ".pytest_cache",
        "dist", "build",
    }

    report = ScanReport(root=root)
    t0 = time.perf_counter()

    py_files: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in ignore_dirs and not d.startswith(".")
        ]
        for fname in filenames:
            if fname.endswith(".py"):
                py_files.append(os.path.join(dirpath, fname))

    for fpath in sorted(py_files):
        result = scan_file(fpath)
        report.results.append(result)

    report.total_ms = (time.perf_counter() - t0) * 1000
    return report


# ─────────────────────────────────────────────
# Report printer
# ─────────────────────────────────────────────

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
SEVERITY_ICON = {
    "CRITICAL": "🔴",
    "HIGH":     "🟠",
    "MEDIUM":   "🟡",
    "LOW":      "🔵",
}


def print_report(report: ScanReport, verbose: bool = False) -> None:
    width = 72
    print("\n" + "═" * width)
    print("  AI BLIND SPOT SCANNER")
    print(f"  Root: {report.root}")
    print("═" * width)

    all_findings = report.all_findings
    by_sev = report.by_severity

    # Summary
    total_files = len(report.results)
    total_findings = len(all_findings)
    critical = len(by_sev.get("CRITICAL", []))
    high = len(by_sev.get("HIGH", []))
    medium = len(by_sev.get("MEDIUM", []))

    print(f"\n  Files scanned : {total_files}")
    print(f"  Files clean   : {report.files_clean}")
    print(f"  Files flagged : {report.files_vulnerable}")
    print(f"  Total findings: {total_findings}")
    print(f"  🔴 CRITICAL   : {critical}")
    print(f"  🟠 HIGH       : {high}")
    print(f"  🟡 MEDIUM     : {medium}")
    real_ms = report.effective_ms
    scan_time_str = f"{real_ms:.1f}ms"
    print(f"  Scan time     : {scan_time_str}")

    # By detector
    print(f"\n{'─' * width}")
    print("  BY DETECTOR")
    print(f"{'─' * width}")
    print(f"  {'Detector':<25} {'Findings':>8}  Description")
    for det_name, findings in sorted(
        report.by_detector.items(),
        key=lambda x: len(x[1]), reverse=True
    ):
        icon = SEVERITY_ICON.get(findings[0].severity, "  ")
        print(f"  {det_name:<25} {len(findings):>8}  {icon}")

    # Findings
    if all_findings:
        print(f"\n{'─' * width}")
        print("  FINDINGS (sorted by severity)")
        print(f"{'─' * width}")

        sorted_findings = sorted(
            all_findings,
            key=lambda f: (SEVERITY_ORDER.get(f.severity, 99), f.file, f.line)
        )

        for f in sorted_findings:
            icon = SEVERITY_ICON.get(f.severity, "  ")
            rel_path = os.path.relpath(f.file, report.root)
            print(f"\n  {icon} [{f.severity}] {f.detector}")
            print(f"     File   : {rel_path}:{f.line}")
            print(f"     Issue  : {f.title}")
            if verbose:
                print(f"     Detail : {f.detail}")
                if f.code_snippet:
                    print("     Code   :")
                    for line in f.code_snippet.splitlines():
                        print(f"              {line}")
                if f.fix_hint:
                    print(f"     Fix    : {f.fix_hint}")

    print(f"\n{'═' * width}")
    if critical > 0:
        print(f"  ⛔  {critical} CRITICAL finding(s) — fix before shipping.")
    elif high > 0:
        print(f"  ⚠️   {high} HIGH finding(s) — review before shipping.")
    elif total_findings == 0:
        print("  ✅  No findings. Clean scan.")
    else:
        print(f"  ℹ️   {medium} MEDIUM finding(s) — low risk but worth reviewing.")
    print("═" * width + "\n")


def export_json(report: ScanReport, output_path: str) -> None:
    """Export report as JSON for CI integration."""
    data = {
        "root": report.root,
        "total_ms": round(report.total_ms, 2),
        "summary": {
            "files_scanned": len(report.results),
            "files_clean": report.files_clean,
            "files_vulnerable": report.files_vulnerable,
            "total_findings": len(report.all_findings),
            "by_severity": {
                sev: len(findings)
                for sev, findings in report.by_severity.items()
            },
        },
        "findings": [
            {
                "file": os.path.relpath(f.file, report.root),
                "line": f.line,
                "detector": f.detector,
                "severity": f.severity,
                "title": f.title,
                "detail": f.detail,
                "fix_hint": f.fix_hint,
            }
            for f in sorted(
                report.all_findings,
                key=lambda f: (SEVERITY_ORDER.get(f.severity, 99), f.file, f.line)
            )
        ],
    }
    Path(output_path).write_text(json.dumps(data, indent=2))
    print(f"JSON report written to: {output_path}")


def export_sarif(report: ScanReport, output_path: str) -> None:
    """
    Export findings as SARIF 2.1.0 for GitHub code scanning.
    Upload to GitHub via: gh code-scanning upload-results --sarif report.sarif
    """
    rules = []
    seen_rules = set()
    results = []

    for f in report.all_findings:
        rule_id = f.detector
        if rule_id not in seen_rules:
            seen_rules.add(rule_id)
            rules.append({
                "id": rule_id,
                "name": rule_id,
                "shortDescription": {"text": f.title},
                "fullDescription": {"text": f.detail},
                "properties": {
                    "tags": ["security", "ai-generated-code"],
                    "severity": f.severity.lower(),
                },
            })

        # SARIF severity mapping
        sarif_level = {
            "CRITICAL": "error",
            "HIGH": "error",
            "MEDIUM": "warning",
            "LOW": "note",
        }.get(f.severity, "warning")

        rel_path = os.path.relpath(f.file, report.root).replace("\\", "/")

        results.append({
            "ruleId": rule_id,
            "level": sarif_level,
            "message": {"text": f"{f.title}. {f.detail}"},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": rel_path,
                        "uriBaseId": "%SRCROOT%",
                    },
                    "region": {
                        "startLine": f.line,
                    },
                }
            }],
            "fixes": [{
                "description": {"text": f.fix_hint},
            }] if f.fix_hint else [],
        })

    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "AI Blind Spot Scanner",
                    "version": "1.0.0",
                    "informationUri": "https://github.com/Emmimal/vibe-scanner/",
                    "rules": rules,
                }
            },
            "results": results,
            "artifacts": [
                {
                    "location": {
                        "uri": os.path.relpath(r.path, report.root).replace("\\", "/"),
                        "uriBaseId": "%SRCROOT%",
                    }
                }
                for r in report.results
            ],
        }],
    }

    Path(output_path).write_text(json.dumps(sarif, indent=2))
    print(f"SARIF report written to: {output_path}")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="AI Blind Spot Scanner — catches what vibe coding misses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scanner.py ./my-project
  python scanner.py ./my-project --verbose
  python scanner.py ./my-project --json report.json
  python scanner.py ./my-project --sarif report.sarif
  python scanner.py ./my-project --fail-on-critical
  python scanner.py ./my-project --fail-on HIGH

CI/CD usage (exits with code 1 if CRITICAL findings exist):
  python scanner.py ./src --fail-on-critical

GitHub code scanning (upload SARIF results):
  python scanner.py ./src --sarif results.sarif
  gh code-scanning upload-results --sarif results.sarif
        """,
    )
    parser.add_argument("path", help="Directory or file to scan")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show code snippets and fix hints")
    parser.add_argument("--json", metavar="FILE",
                        help="Export findings as JSON")
    parser.add_argument("--sarif", metavar="FILE",
                        help="Export findings as SARIF 2.1.0 (for GitHub code scanning)")
    parser.add_argument("--fail-on-critical", action="store_true",
                        help="Exit with code 1 if any CRITICAL findings exist (CI/CD use)")
    parser.add_argument("--fail-on", metavar="SEVERITY",
                        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                        help="Exit with code 1 if findings at this severity or above")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"ERROR: path does not exist: {args.path}")
        sys.exit(1)

    if target.is_file():
        result = scan_file(str(target))
        report = ScanReport(root=str(target.parent), results=[result])
    else:
        report = scan_directory(str(target))

    print_report(report, verbose=args.verbose)

    if args.json:
        export_json(report, args.json)

    if args.sarif:
        export_sarif(report, args.sarif)

    # --fail-on-critical shortcut
    if args.fail_on_critical:
        has_critical = any(
            f.severity == "CRITICAL"
            for f in report.all_findings
        )
        if has_critical:
            sys.exit(1)

    # --fail-on SEVERITY
    if args.fail_on:
        threshold = SEVERITY_ORDER[args.fail_on]
        has_blocking = any(
            SEVERITY_ORDER.get(f.severity, 99) <= threshold
            for f in report.all_findings
        )
        if has_blocking:
            sys.exit(1)


if __name__ == "__main__":
    main()
