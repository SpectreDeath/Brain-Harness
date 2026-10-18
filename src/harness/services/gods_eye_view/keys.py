"""God's Eye View service keys."""

from __future__ import annotations

from typing import TYPE_CHECKING
from harness.kernel.context import ServiceKey

if TYPE_CHECKING:
    from .protocols import GodsEyeViewService

GODS_EYE_VIEW_SERVICE_KEY: ServiceKey[GodsEyeViewService] = ServiceKey("service.gods_eye_view")

__all__ = ["GODS_EYE_VIEW_SERVICE_KEY"]
