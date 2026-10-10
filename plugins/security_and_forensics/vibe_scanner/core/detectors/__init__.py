"""Seven core AST vulnerability detectors subpackage (decomposed)."""

from __future__ import annotations

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
from plugins.security_and_forensics.vibe_scanner.core.detectors.registry import (
    DETECTORS,
    get_default_detectors,
)
from plugins.security_and_forensics.vibe_scanner.core.detectors.secrets import (
    HardcodedSecretDetector,
)
from plugins.security_and_forensics.vibe_scanner.core.detectors.sql_injection import (
    SQLInjectionDetector,
)

__all__ = [
    "DETECTORS",
    "ExceptionSwallowedDetector",
    "HardcodedSecretDetector",
    "InputValidationDetector",
    "SQLInjectionDetector",
    "UnsafeDeserialiseDetector",
    "UnsafeFileAccessDetector",
    "WeakCryptoDetector",
    "get_default_detectors",
]
