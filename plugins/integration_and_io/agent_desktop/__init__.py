"""Agent Desktop plugin package."""
from .main import (
    AgentDesktopPlugin,
    desktop_act,
    desktop_find,
    desktop_manage_window,
    desktop_snapshot,
    desktop_status,
    desktop_wait,
    plugin,
)

__all__ = [
    "AgentDesktopPlugin",
    "plugin",
    "desktop_snapshot",
    "desktop_act",
    "desktop_find",
    "desktop_manage_window",
    "desktop_wait",
    "desktop_status",
]
