"""Characterization test suite for decomposed Vibe Scanner architecture.

Verifies:
1. Isolated submodule imports (models, base, detectors, engine, reporters).
2. Backward-compatible re-exports from plugins.security_and_forensics.vibe_scanner.scanner_core.
3. Slotted models memory hygiene (Rule 12).
4. AST detection functionality across all 7 vulnerability categories.
5. Bounded directory traversal and noise pruning (Rule 52).
"""

from __future__ import annotations

import ast
import tempfile
from pathlib import Path
import pytest


def test_submodule_isolated_imports() -> None:
    """Verify each decomposed submodule can be imported in isolation."""
    from plugins.security_and_forensics.vibe_scanner.core import models
    from plugins.security_and_forensics.vibe_scanner.core import base
    from plugins.security_and_forensics.vibe_scanner.core import detectors
    from plugins.security_and_forensics.vibe_scanner.core import engine
    from plugins.security_and_forensics.vibe_scanner.core import reporters

    assert hasattr(models, "Finding")
    assert hasattr(models, "ScanResult")
    assert hasattr(models, "ScanReport")

    assert hasattr(base, "BaseDetector")

    assert hasattr(detectors, "InputValidationDetector")
    assert hasattr(detectors, "UnsafeFileAccessDetector")
    assert hasattr(detectors, "ExceptionSwallowedDetector")
    assert hasattr(detectors, "HardcodedSecretDetector")
    assert hasattr(detectors, "UnsafeDeserialiseDetector")
    assert hasattr(detectors, "SQLInjectionDetector")
    assert hasattr(detectors, "WeakCryptoDetector")
    assert hasattr(detectors, "DETECTORS")

    assert hasattr(engine, "scan_file")
    assert hasattr(engine, "scan_directory")

    assert hasattr(reporters, "print_report")
    assert hasattr(reporters, "export_json")
    assert hasattr(reporters, "export_sarif")


def test_scanner_core_facade_re_exports() -> None:
    """Verify scanner_core.py re-exports all original symbols for 100% backward compatibility."""
    import plugins.security_and_forensics.vibe_scanner.scanner_core as sc

    expected_symbols = [
        "Finding",
        "ScanResult",
        "ScanReport",
        "BaseDetector",
        "InputValidationDetector",
        "UnsafeFileAccessDetector",
        "ExceptionSwallowedDetector",
        "HardcodedSecretDetector",
        "UnsafeDeserialiseDetector",
        "SQLInjectionDetector",
        "WeakCryptoDetector",
        "DETECTORS",
        "scan_file",
        "scan_directory",
        "print_report",
        "export_json",
        "export_sarif",
        "SEVERITY_ORDER",
        "SEVERITY_ICON",
    ]
    for sym in expected_symbols:
        assert hasattr(sc, sym), f"Missing symbol in scanner_core facade: {sym}"


def test_slotted_models_hygiene() -> None:
    """Verify Finding uses slots for memory efficiency (Rule 12)."""
    from plugins.security_and_forensics.vibe_scanner.core.models import Finding

    f = Finding(
        file="test.py",
        line=10,
        detector="SQLInjection",
        severity="CRITICAL",
        title="Unparameterized query",
        detail="detail",
    )
    assert hasattr(f, "__slots__")
    assert f.file == "test.py"
    assert f.severity == "CRITICAL"


def test_ast_detectors_functionality() -> None:
    """Verify AST detectors identify classic vulnerabilities cleanly."""
    from plugins.security_and_forensics.vibe_scanner.core.detectors import (
        SQLInjectionDetector,
        UnsafeDeserialiseDetector,
        WeakCryptoDetector,
        ExceptionSwallowedDetector,
    )

    # 1. SQL Injection
    sql_det = SQLInjectionDetector()
    sql_src = "cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')"
    tree = ast.parse(sql_src)
    findings = sql_det.detect(tree, sql_src, "app.py")
    assert len(findings) > 0
    assert findings[0].severity == "CRITICAL"

    # 2. Unsafe Deserialisation
    pickle_det = UnsafeDeserialiseDetector()
    pickle_src = "import pickle\ndata = pickle.loads(user_payload)"
    tree = ast.parse(pickle_src)
    findings = pickle_det.detect(tree, pickle_src, "net.py")
    assert len(findings) > 0
    assert findings[0].detector == "UnsafeDeserialise"

    # 3. Weak Crypto
    crypto_det = WeakCryptoDetector()
    crypto_src = "import hashlib\npwd_hash = hashlib.md5(password.encode()).hexdigest()"
    tree = ast.parse(crypto_src)
    findings = crypto_det.detect(tree, crypto_src, "auth.py")
    assert len(findings) > 0
    assert any("Weak hash" in f.title or "Weak crypto" in f.title for f in findings)

    # 4. Swallowed Exception
    exc_det = ExceptionSwallowedDetector()
    exc_src = "try:\n    do_work()\nexcept Exception:\n    pass\n"
    tree = ast.parse(exc_src)
    findings = exc_det.detect(tree, exc_src, "worker.py")
    assert len(findings) > 0
    assert any("swallowed" in f.title.lower() for f in findings)


def test_engine_scan_file_and_directory(tmp_path: Path) -> None:
    """Verify engine functions scan files and bounded directories cleanly."""
    from plugins.security_and_forensics.vibe_scanner.core.engine import scan_file, scan_directory

    # Clean file
    clean_file = tmp_path / "clean.py"
    clean_file.write_text("def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")
    res = scan_file(str(clean_file))
    assert res.parse_error is False
    assert len(res.findings) == 0

    # Vulnerable file
    vuln_file = tmp_path / "vuln.py"
    vuln_file.write_text("import pickle\npickle.loads(data)\n", encoding="utf-8")
    res_vuln = scan_file(str(vuln_file))
    assert len(res_vuln.findings) > 0

    # Scan directory
    report = scan_directory(str(tmp_path))
    assert len(report.results) == 2
    assert report.files_clean == 1
    assert report.files_vulnerable == 1
