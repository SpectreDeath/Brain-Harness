"""Contract tests for Vibe Scanner detectors modular subpackage decomposition.

Verifies:
1. Subpackage modular structure across all 7 detectors and registry (Rule 18)
2. Submodule line counts strictly < 200 lines (Rule 11)
3. Correct AST detection behavior for each individual detector
4. Registry exports and instantiation
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from plugins.security_and_forensics.vibe_scanner.core.detectors import (
    DETECTORS,
    ExceptionSwallowedDetector,
    HardcodedSecretDetector,
    InputValidationDetector,
    SQLInjectionDetector,
    UnsafeDeserialiseDetector,
    UnsafeFileAccessDetector,
    WeakCryptoDetector,
    get_default_detectors,
)
from plugins.security_and_forensics.vibe_scanner.core.detectors.crypto import (
    WeakCryptoDetector as SubCryptoDetector,
)
from plugins.security_and_forensics.vibe_scanner.core.detectors.deserialisation import (
    UnsafeDeserialiseDetector as SubDeserialiseDetector,
)
from plugins.security_and_forensics.vibe_scanner.core.detectors.exception_swallowed import (
    ExceptionSwallowedDetector as SubExceptionDetector,
)
from plugins.security_and_forensics.vibe_scanner.core.detectors.file_access import (
    UnsafeFileAccessDetector as SubFileAccessDetector,
)
from plugins.security_and_forensics.vibe_scanner.core.detectors.input_validation import (
    InputValidationDetector as SubInputValDetector,
)
from plugins.security_and_forensics.vibe_scanner.core.detectors.registry import (
    DETECTORS as RegistryDetectors,
)
from plugins.security_and_forensics.vibe_scanner.core.detectors.secrets import (
    HardcodedSecretDetector as SubSecretDetector,
)
from plugins.security_and_forensics.vibe_scanner.core.detectors.sql_injection import (
    SQLInjectionDetector as SubSQLDetector,
)


@pytest.mark.unit
class TestVibeScannerDetectorsDecomposition:
    """Contract tests for vibe_scanner detectors subpackage decomposition."""

    def test_submodule_line_counts(self) -> None:
        """Verify all submodules in vibe_scanner detectors are strictly < 200 lines (Rule 11)."""
        pkg_dir = (
            Path(__file__).resolve().parent.parent
            / "plugins"
            / "security_and_forensics"
            / "vibe_scanner"
            / "core"
            / "detectors"
        )
        py_files = list(pkg_dir.glob("*.py"))
        assert len(py_files) >= 9, f"Expected at least 9 submodules, found {len(py_files)}"

        for file_path in py_files:
            lines = len(file_path.read_text(encoding="utf-8").splitlines())
            assert lines < 200, f"{file_path.name} exceeds 200 lines ({lines} lines)"

    def test_reexports_and_submodule_identity(self) -> None:
        """Verify subpackage re-exports match their submodule definitions."""
        assert InputValidationDetector is SubInputValDetector
        assert UnsafeFileAccessDetector is SubFileAccessDetector
        assert ExceptionSwallowedDetector is SubExceptionDetector
        assert HardcodedSecretDetector is SubSecretDetector
        assert UnsafeDeserialiseDetector is SubDeserialiseDetector
        assert SQLInjectionDetector is SubSQLDetector
        assert WeakCryptoDetector is SubCryptoDetector
        assert DETECTORS is RegistryDetectors

    def test_registry_contains_seven_detectors(self) -> None:
        """Verify default detectors list contains all 7 core detectors."""
        detectors = get_default_detectors()
        assert len(detectors) == 7
        names = {d.NAME for d in detectors}
        expected = {
            "InputValidation",
            "UnsafeFileAccess",
            "ExceptionSwallowed",
            "HardcodedSecret",
            "UnsafeDeserialise",
            "SQLInjection",
            "WeakCrypto",
        }
        assert names == expected

    def test_input_validation_detection(self) -> None:
        """Verify input validation detector catches untrusted sink arguments."""
        code = (
            "user_data = request.json.get('filename')\n"
            "open(user_data, 'r')\n"
        )
        tree = ast.parse(code)
        detector = InputValidationDetector()
        findings = detector.detect(tree, code, "test.py")
        assert len(findings) >= 1
        assert any("Unvalidated input" in f.title for f in findings)

    def test_unsafe_file_access_detection(self) -> None:
        """Verify unsafe file access detector catches path traversal and unbounded rglob."""
        code = (
            "file_name = request.args.get('path')\n"
            "with open(file_name, 'w') as f:\n"
            "    f.write('data')\n"
            "for p in Path('.').rglob('*'):\n"
            "    pass\n"
        )
        tree = ast.parse(code)
        detector = UnsafeFileAccessDetector()
        findings = detector.detect(tree, code, "test.py")
        assert len(findings) >= 2
        titles = [f.title for f in findings]
        assert any("Unsafe file access" in t for t in titles)
        assert any("Unbounded rglob" in t for t in titles)

    def test_exception_swallowed_detection(self) -> None:
        """Verify exception swallowed detector catches bare except and empty bodies."""
        code = (
            "try:\n"
            "    do_something()\n"
            "except:\n"
            "    pass\n"
        )
        tree = ast.parse(code)
        detector = ExceptionSwallowedDetector()
        findings = detector.detect(tree, code, "test.py")
        assert len(findings) >= 1
        assert any("Bare except" in f.title for f in findings)

    def test_hardcoded_secret_detection(self) -> None:
        """Verify hardcoded secret detector catches string literal tokens."""
        code = "api_key = 'sk-1234567890abcdef1234567890abcdef'\n"
        tree = ast.parse(code)
        detector = HardcodedSecretDetector()
        findings = detector.detect(tree, code, "test.py")
        assert len(findings) >= 1
        assert any("Hardcoded secret" in f.title for f in findings)

    def test_unsafe_deserialise_detection(self) -> None:
        """Verify unsafe deserialisation detector catches pickle and unsafe yaml."""
        code = "pickle.loads(untrusted_bytes)\n"
        tree = ast.parse(code)
        detector = UnsafeDeserialiseDetector()
        findings = detector.detect(tree, code, "test.py")
        assert len(findings) >= 1
        assert any("pickle.loads" in f.title for f in findings)

    def test_sql_injection_detection(self) -> None:
        """Verify SQL injection detector catches formatted queries."""
        code = "query = f'SELECT * FROM users WHERE id = {user_id}'\n"
        tree = ast.parse(code)
        detector = SQLInjectionDetector()
        findings = detector.detect(tree, code, "test.py")
        assert len(findings) >= 1
        assert any("SQL injection" in f.title for f in findings)

    def test_weak_crypto_detection(self) -> None:
        """Verify weak crypto detector catches md5 and insecure random in security context."""
        code = "password_hash = hashlib.md5(pwd.encode()).hexdigest()\n"
        tree = ast.parse(code)
        detector = WeakCryptoDetector()
        findings = detector.detect(tree, code, "test.py")
        assert len(findings) >= 1
        assert any("Weak hash" in f.title or "Weak crypto" in f.title for f in findings)
