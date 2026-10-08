"""Core engine package for Vibe Scanner (decomposed)."""

from __future__ import annotations

from plugins.security_and_forensics.vibe_scanner.core.base import BaseDetector
from plugins.security_and_forensics.vibe_scanner.core.detectors import (
    DETECTORS,
    ExceptionSwallowedDetector,
    HardcodedSecretDetector,
    InputValidationDetector,
    SQLInjectionDetector,
    UnsafeDeserialiseDetector,
    UnsafeFileAccessDetector,
    WeakCryptoDetector,
)
from plugins.security_and_forensics.vibe_scanner.core.engine import (
    scan_directory,
    scan_file,
)
from plugins.security_and_forensics.vibe_scanner.core.models import (
    Finding,
    ScanReport,
    ScanResult,
)
from plugins.security_and_forensics.vibe_scanner.core.reporters import (
    SEVERITY_ICON,
    SEVERITY_ORDER,
    export_json,
    export_sarif,
    print_report,
)

__all__ = [
    "DETECTORS",
    "BaseDetector",
    "ExceptionSwallowedDetector",
    "Finding",
    "HardcodedSecretDetector",
    "InputValidationDetector",
    "SQLInjectionDetector",
    "SEVERITY_ICON",
    "SEVERITY_ORDER",
    "ScanReport",
    "ScanResult",
    "UnsafeDeserialiseDetector",
    "UnsafeFileAccessDetector",
    "WeakCryptoDetector",
    "export_json",
    "export_sarif",
    "print_report",
    "scan_directory",
    "scan_file",
]
