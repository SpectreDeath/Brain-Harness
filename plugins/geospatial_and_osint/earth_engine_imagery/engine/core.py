"""Base initialization and Earth Engine environment bindings."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any
import structlog

logger = structlog.get_logger(__name__)

# Ensure Google Earth Engine source repository is accessible if cloned
_POSSIBLE_EE_PATHS = [
    Path(r"D:\GitHub\cloned\Google\earthengine-api\python"),
    Path(__file__).parent.parent / "vendor",
]
for _p in _POSSIBLE_EE_PATHS:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    import ee  # type: ignore
    _EE_AVAILABLE = True
except Exception as _err:
    logger.debug("earth_engine_import_offline", error=str(_err))
    _EE_AVAILABLE = False
    ee = None  # type: ignore


class BaseEarthEngine:
    """Base class providing lazy initialization and authentication checks for Google Earth Engine."""

    def __init__(self) -> None:
        self._ee_initialized: bool = False

    def _ensure_initialized(self) -> bool:
        """Attempt silent initialization of Earth Engine API if credentials exist."""
        if not self._ee_initialized and _EE_AVAILABLE and ee is not None:
            try:
                ee.Initialize()
                self._ee_initialized = True
            except Exception as e:
                logger.debug("earth_engine_auth_not_initialized", reason=str(e))
                self._ee_initialized = False
        return self._ee_initialized

    @property
    def is_live_available(self) -> bool:
        """Check if live Earth Engine API is initialized and available."""
        return self._ensure_initialized()
