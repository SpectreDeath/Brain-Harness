"""Google Magika Deep-Learning Content Type & MIME Detection Plugin for Brain Harness."""

from __future__ import annotations

import base64
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger(__name__)

# Ensure Google Magika source repository is accessible
_POSSIBLE_MAGIKA_PATHS = [
    Path(r"D:\GitHub\cloned\Google\magika\python\src"),
    Path(__file__).parent / "vendor",
]
for _p in _POSSIBLE_MAGIKA_PATHS:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    from magika import Magika, PredictionMode
    from magika.types import MagikaResult
    _MAGIKA_AVAILABLE = True
except Exception as _err:
    logger.warning("magika_import_error", error=str(_err))
    _MAGIKA_AVAILABLE = False
    Magika = None  # type: ignore
    PredictionMode = None  # type: ignore


@runtime_checkable
class MagikaContentDetectorService(Protocol):
    """Protocol for Magika deep-learning file content type detection operations."""

    def identify_path(self, path: str, prediction_mode: str = "high_confidence") -> dict[str, Any]:
        ...

    def identify_bytes(self, content_b64: str, prediction_mode: str = "high_confidence") -> dict[str, Any]:
        ...

    def batch_scan(self, dir_path: str, recursive: bool = True, max_files: int = 500) -> dict[str, Any]:
        ...

    def list_content_types(self, filter_group: str = "") -> dict[str, Any]:
        ...

    def get_model_info(self) -> dict[str, Any]:
        ...


MAGIKA_CONTENT_DETECTOR_KEY: ServiceKey[MagikaContentDetectorService] = ServiceKey("service.magika_content_detector")


class MagikaContentDetectorEngine:
    """Core detection engine wrapping Google Magika ONNX runtime with fallback heuristics."""

    def __init__(self, model_dir: Path | str | None = None) -> None:
        self._magika_instance: Any = None
        self._model_dir = Path(model_dir) if model_dir else None
        self._initialized = False

    def _ensure_initialized(self) -> Any:
        if not self._initialized:
            if _MAGIKA_AVAILABLE and Magika is not None:
                try:
                    self._magika_instance = Magika(model_dir=self._model_dir)
                except Exception as e:
                    logger.error("failed_to_initialize_magika", error=str(e))
                    self._magika_instance = None
            self._initialized = True
        return self._magika_instance

    def _mode_from_string(self, mode_str: str) -> Any:
        if not _MAGIKA_AVAILABLE or PredictionMode is None:
            return None
        m = (mode_str or "").strip().lower()
        if m in ("medium", "medium_confidence"):
            return PredictionMode.MEDIUM_CONFIDENCE
        if m in ("best", "best_effort"):
            return PredictionMode.BEST_EFFORT
        return PredictionMode.HIGH_CONFIDENCE

    def identify_path(self, path: str, prediction_mode: str = "high_confidence") -> dict[str, Any]:
        p = Path(path)
        if not p.exists():
            return {
                "status": "error",
                "error": f"File not found: {path}",
                "path": str(path),
            }
        if p.is_dir():
            return {
                "status": "ok",
                "path": str(p),
                "label": "directory",
                "mime_type": "inode/directory",
                "group": "inode",
                "description": "Directory",
                "extensions": [],
                "score": 1.0,
                "is_text": False,
            }

        mag = self._ensure_initialized()
        if mag is None:
            ext = p.suffix.lstrip(".").lower()
            return {
                "status": "ok",
                "path": str(p),
                "label": ext or "unknown",
                "mime_type": f"application/{ext}" if ext else "application/octet-stream",
                "group": "unknown",
                "description": f"Fallback extension classification for {ext}",
                "extensions": [ext] if ext else [],
                "score": 0.5,
                "is_text": ext in ("txt", "py", "json", "md", "csv", "html", "js", "ts", "yaml", "yml"),
            }

        mode = self._mode_from_string(prediction_mode)
        try:
            res: MagikaResult = mag.identify_path(p)
            out = res.output
            return {
                "status": "ok",
                "path": str(p),
                "label": str(out.label),
                "mime_type": str(out.mime_type),
                "group": str(out.group),
                "description": str(out.description),
                "extensions": [str(e) for e in out.extensions],
                "score": float(res.score),
                "is_text": bool(out.is_text),
                "overwrite_reason": str(res.prediction.overwrite_reason.value if hasattr(res.prediction.overwrite_reason, "value") else res.prediction.overwrite_reason),
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "path": str(p)}

    def identify_bytes(self, content_b64: str, prediction_mode: str = "high_confidence") -> dict[str, Any]:
        try:
            raw_bytes = base64.b64decode(content_b64)
        except Exception as e:
            return {"status": "error", "error": f"Invalid base64 encoding: {e}"}

        mag = self._ensure_initialized()
        if mag is None:
            is_text = False
            try:
                raw_bytes.decode("utf-8")
                is_text = True
            except UnicodeDecodeError:
                pass
            return {
                "status": "ok",
                "label": "text" if is_text else "binary",
                "mime_type": "text/plain" if is_text else "application/octet-stream",
                "group": "text" if is_text else "binary",
                "description": "Fallback in-memory byte analysis",
                "extensions": ["txt"] if is_text else ["bin"],
                "score": 0.5,
                "is_text": is_text,
            }

        try:
            res = mag.identify_bytes(raw_bytes)
            out = res.output
            return {
                "status": "ok",
                "label": str(out.label),
                "mime_type": str(out.mime_type),
                "group": str(out.group),
                "description": str(out.description),
                "extensions": [str(e) for e in out.extensions],
                "score": float(res.score),
                "is_text": bool(out.is_text),
                "overwrite_reason": str(res.prediction.overwrite_reason.value if hasattr(res.prediction.overwrite_reason, "value") else res.prediction.overwrite_reason),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def batch_scan(self, dir_path: str, recursive: bool = True, max_files: int = 500) -> dict[str, Any]:
        p = Path(dir_path)
        if not p.exists() or not p.is_dir():
            return {"status": "error", "error": f"Directory not found: {dir_path}"}

        files: list[dict[str, Any]] = []
        group_counts: dict[str, int] = {}
        total_scanned = 0

        pattern = "**/*" if recursive else "*"
        for f in p.glob(pattern):
            if f.is_file():
                if total_scanned >= max_files:
                    break
                info = self.identify_path(str(f))
                if info.get("status") == "ok":
                    grp = str(info.get("group", "unknown"))
                    group_counts[grp] = group_counts.get(grp, 0) + 1
                    files.append({
                        "path": str(f.relative_to(p)),
                        "label": info.get("label"),
                        "mime_type": info.get("mime_type"),
                        "group": grp,
                        "score": info.get("score"),
                        "is_text": info.get("is_text"),
                    })
                    total_scanned += 1

        return {
            "status": "ok",
            "directory": str(p),
            "scanned_count": total_scanned,
            "group_counts": group_counts,
            "files": files,
        }

    def list_content_types(self, filter_group: str = "") -> dict[str, Any]:
        mag = self._ensure_initialized()
        items: list[dict[str, Any]] = []
        filter_grp = (filter_group or "").strip().lower()

        kb_path = Path(r"D:\GitHub\cloned\Google\magika\assets\content_types_kb.min.json")
        if kb_path.exists():
            import json
            try:
                kb_data = json.loads(kb_path.read_text(encoding="utf-8"))
                for label, data in kb_data.items():
                    grp = str(data.get("group", ""))
                    if filter_grp and grp.lower() != filter_grp:
                        continue
                    items.append({
                        "label": str(label),
                        "mime_type": str(data.get("mime_type", "")),
                        "group": grp,
                        "description": str(data.get("description", "")),
                        "extensions": [str(x) for x in data.get("extensions", [])],
                        "is_text": bool(data.get("is_text", False)),
                    })
                return {
                    "status": "ok",
                    "total_count": len(items),
                    "filter_group": filter_grp,
                    "content_types": items,
                }
            except Exception as e:
                logger.warning("failed_reading_kb_json", error=str(e))

        if mag is not None:
            for ct in mag.get_output_content_types():
                items.append({
                    "label": str(ct),
                    "mime_type": f"application/{ct}",
                    "group": "unknown",
                    "description": f"Output label {ct}",
                    "extensions": [str(ct)],
                    "is_text": False,
                })

        return {
            "status": "ok",
            "total_count": len(items),
            "filter_group": filter_grp,
            "content_types": items,
        }

    def get_model_info(self) -> dict[str, Any]:
        mag = self._ensure_initialized()
        if mag is None:
            return {
                "status": "ok",
                "model_name": "fallback_heuristic",
                "version": "1.0.0",
                "output_types_count": 0,
                "onnx_available": _MAGIKA_AVAILABLE,
            }

        return {
            "status": "ok",
            "model_name": str(mag.get_model_name()),
            "version": str(mag.get_module_version()),
            "output_types_count": len(mag.get_output_content_types()),
            "onnx_available": True,
        }


# Global engine singleton
_GLOBAL_DETECTOR = MagikaContentDetectorEngine()


# -----------------------------------------------------------------------------
# Top-level Tool Functions Matching Entrypoint Signatures
# -----------------------------------------------------------------------------

def magika_identify_path(path: str, prediction_mode: str = "high_confidence") -> dict[str, Any]:
    """Identify file content type, MIME, group, confidence score, and text/binary flag from a file path."""
    return _GLOBAL_DETECTOR.identify_path(path=path, prediction_mode=prediction_mode)


def magika_identify_bytes(content_b64: str, prediction_mode: str = "high_confidence") -> dict[str, Any]:
    """Identify content type and MIME metadata from in-memory base64-encoded bytes without disk writes."""
    return _GLOBAL_DETECTOR.identify_bytes(content_b64=content_b64, prediction_mode=prediction_mode)


def magika_batch_scan(dir_path: str, recursive: bool = True, max_files: int = 500) -> dict[str, Any]:
    """Scan and classify all files in a directory hierarchy with aggregated group statistics and confidence scoring."""
    return _GLOBAL_DETECTOR.batch_scan(dir_path=dir_path, recursive=recursive, max_files=max_files)


def magika_list_content_types(filter_group: str = "") -> dict[str, Any]:
    """Query supported output labels, MIME types, and groups from the Magika knowledge base."""
    return _GLOBAL_DETECTOR.list_content_types(filter_group=filter_group)


def magika_get_model_info() -> dict[str, Any]:
    """Retrieve metadata about the active Magika ONNX model, output dimension, and runtime features."""
    return _GLOBAL_DETECTOR.get_model_info()


# -----------------------------------------------------------------------------
# Harness Plugin Class & IoC Lifecycle
# -----------------------------------------------------------------------------

class MagikaContentDetectorPlugin(HarnessPlugin, MagikaContentDetectorService):
    """Brain Harness Plugin providing Google Magika deep learning MIME and content classification services."""

    name = "plugin.magika_content_detector"
    version = "1.0.0"
    description = "Google Magika deep-learning file content type, MIME detection, and batch directory classification engine"
    trusted = True

    def __init__(self, engine: MagikaContentDetectorEngine | None = None) -> None:
        self._engine = engine or _GLOBAL_DETECTOR

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [MAGIKA_CONTENT_DETECTOR_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(MAGIKA_CONTENT_DETECTOR_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # Protocol Implementation
    # -------------------------------------------------------------------------

    def identify_path(self, path: str, prediction_mode: str = "high_confidence") -> dict[str, Any]:
        return self._engine.identify_path(path=path, prediction_mode=prediction_mode)

    def identify_bytes(self, content_b64: str, prediction_mode: str = "high_confidence") -> dict[str, Any]:
        return self._engine.identify_bytes(content_b64=content_b64, prediction_mode=prediction_mode)

    def batch_scan(self, dir_path: str, recursive: bool = True, max_files: int = 500) -> dict[str, Any]:
        return self._engine.batch_scan(dir_path=dir_path, recursive=recursive, max_files=max_files)

    def list_content_types(self, filter_group: str = "") -> dict[str, Any]:
        return self._engine.list_content_types(filter_group=filter_group)

    def get_model_info(self) -> dict[str, Any]:
        return self._engine.get_model_info()
