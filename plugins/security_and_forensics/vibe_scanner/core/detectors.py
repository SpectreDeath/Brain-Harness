"""Seven core AST vulnerability detectors targeting AI code blind spots."""

from __future__ import annotations

import ast
import re
from typing import Dict, List

from plugins.security_and_forensics.vibe_scanner.core.base import BaseDetector
from plugins.security_and_forensics.vibe_scanner.core.models import Finding

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


__all__ = [
    "DETECTORS",
    "ExceptionSwallowedDetector",
    "HardcodedSecretDetector",
    "InputValidationDetector",
    "SQLInjectionDetector",
    "UnsafeDeserialiseDetector",
    "UnsafeFileAccessDetector",
    "WeakCryptoDetector",
]
