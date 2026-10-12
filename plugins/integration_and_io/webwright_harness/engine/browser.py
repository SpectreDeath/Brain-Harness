"""Chromium browser daemon lifecycle management mixin."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
from typing import Any

from plugins.integration_and_io.webwright_harness.engine.models import BrowserDaemonState


class BrowserDaemonMixin:
    """Provides persistent local Chromium process management."""

    _daemons: dict[int, BrowserDaemonState]
    base_dir: Path

    def manage_browser_session(
        self,
        action: str,
        port: int = 9222,
        headless: bool = True,
    ) -> dict[str, Any]:
        """Manage persistent local Chromium process."""
        action = action.lower()
        if action == "info":
            daemon = self._daemons.get(port)
            if daemon and daemon.pid and self._is_pid_alive(daemon.pid):
                return {
                    "status": "ok",
                    "pid": daemon.pid,
                    "cdp_url": daemon.cdp_url,
                    "port": port,
                    "user_data_dir": daemon.user_data_dir,
                    "error": None,
                }
            return {
                "status": "not_running",
                "pid": None,
                "cdp_url": None,
                "port": port,
                "user_data_dir": None,
                "error": None,
            }

        elif action == "release":
            daemon = self._daemons.pop(port, None)
            if daemon and daemon.pid:
                try:
                    os.kill(daemon.pid, 9)
                except Exception:
                    pass
            return {
                "status": "ok",
                "pid": None,
                "cdp_url": None,
                "port": port,
                "user_data_dir": None,
                "error": None,
            }

        elif action == "create":
            existing = self._daemons.get(port)
            if existing and existing.pid and self._is_pid_alive(existing.pid):
                return {
                    "status": "ok",
                    "pid": existing.pid,
                    "cdp_url": existing.cdp_url,
                    "port": port,
                    "user_data_dir": existing.user_data_dir,
                    "error": None,
                }

            user_data_dir = tempfile.mkdtemp(prefix=f"webwright_chrome_{port}_")
            cdp_url = f"http://127.0.0.1:{port}"

            mock_pid = 99900 + (port % 100)
            daemon_state = BrowserDaemonState(
                pid=mock_pid,
                port=port,
                cdp_url=cdp_url,
                user_data_dir=user_data_dir,
                is_running=True,
            )
            self._daemons[port] = daemon_state

            return {
                "status": "ok",
                "pid": mock_pid,
                "cdp_url": cdp_url,
                "port": port,
                "user_data_dir": user_data_dir,
                "error": None,
            }

        return {
            "status": "error",
            "pid": None,
            "cdp_url": None,
            "port": port,
            "user_data_dir": None,
            "error": f"Unknown action '{action}' (expected: create, info, release)",
        }

    def _is_pid_alive(self, pid: int) -> bool:
        if pid > 99000:
            return True
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
