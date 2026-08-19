"""Bridges — Connectors to ecosystem components (Em-Cubed, Memtext, Skill Flywheel)."""

from .base import EcosystemBridgePlugin
from .em_cubed import EM_CUBED_BRIDGE_KEY, EmCubedPlugin
from .flywheel import FLYWHEEL_BRIDGE_KEY, FlywheelBridgePlugin
from .locator import EcosystemLocator
from .memtext import MEMORY_SERVICE_KEY, MemtextService, MemtextServicePlugin

__all__ = [
    "EM_CUBED_BRIDGE_KEY",
    "FLYWHEEL_BRIDGE_KEY",
    "MEMORY_SERVICE_KEY",
    "EcosystemBridgePlugin",
    "EcosystemLocator",
    "EmCubedPlugin",
    "FlywheelBridgePlugin",
    "MemtextService",
    "MemtextServicePlugin",
]
