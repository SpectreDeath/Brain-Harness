"""Detector registry and default detector collection."""

from __future__ import annotations

from typing import List

from plugins.security_and_forensics.vibe_scanner.core.base import BaseDetector
from plugins.security_and_forensics.vibe_scanner.core.detectors.crypto import (
    WeakCryptoDetector,
)
from plugins.security_and_forensics.vibe_scanner.core.detectors.deserialisation import (
    UnsafeDeserialiseDetector,
)
from plugins.security_and_forensics.vibe_scanner.core.detectors.exception_swallowed import (
    ExceptionSwallowedDetector,
)
from plugins.security_and_forensics.vibe_scanner.core.detectors.file_access import (
    UnsafeFileAccessDetector,
)
from plugins.security_and_forensics.vibe_scanner.core.detectors.input_validation import (
    InputValidationDetector,
)
from plugins.security_and_forensics.vibe_scanner.core.detectors.secrets import (
    HardcodedSecretDetector,
)
from plugins.security_and_forensics.vibe_scanner.core.detectors.sql_injection import (
    SQLInjectionDetector,
)


def get_default_detectors() -> List[BaseDetector]:
    """Instantiate and return the 7 core vulnerability detectors."""
    return [
        InputValidationDetector(),
        UnsafeFileAccessDetector(),
        ExceptionSwallowedDetector(),
        HardcodedSecretDetector(),
        UnsafeDeserialiseDetector(),
        SQLInjectionDetector(),
        WeakCryptoDetector(),
    ]


DETECTORS: List[BaseDetector] = get_default_detectors()

__all__ = ["DETECTORS", "get_default_detectors"]
