"""State persistence mixin for Repository Dock registry records."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

from .models import DockError
from .protocols import logger


class _DockStoreMixin:
    """Mixin handling atomic loading, quarantine, and persistence of docks.json."""

    _state_file: Path

    def _load_records(self) -> dict[str, dict[str, Any]]:
        if not self._state_file.exists():
            return {}
        try:
            content = self._state_file.read_text(encoding="utf-8")
            if not content.strip():
                return {}
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError("docks.json root is not a dictionary")
            return data
        except Exception as e:
            ts = int(time.time())
            quarantine_path = self._state_file.with_name(f"{self._state_file.name}.corrupt-{ts}")
            try:
                shutil.copy2(self._state_file, quarantine_path)
            except Exception:
                pass
            logger.error(
                "docks.json is corrupted; quarantined to backup and refusing destructive overwrite",
                state_file=str(self._state_file),
                quarantine=str(quarantine_path),
                error=str(e),
            )
            raise DockError(f"docks.json is corrupted and quarantined to {quarantine_path.name}: {e}") from e

    def _save_records(self, records: dict[str, dict[str, Any]]) -> None:
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self._state_file.with_suffix(".tmp")
        temp_file.write_text(json.dumps(records, indent=2), encoding="utf-8")
        temp_file.replace(self._state_file)


__all__ = ["_DockStoreMixin"]
