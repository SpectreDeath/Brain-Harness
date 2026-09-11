"""Google Magika Format Forensics & Polyglot Security Plugin for Brain Harness."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from plugins.security_and_forensics.magika_content_detector.main import (
    MAGIKA_CONTENT_DETECTOR_KEY,
    MagikaContentDetectorEngine,
    _GLOBAL_DETECTOR,
)

logger = structlog.get_logger(__name__)


@runtime_checkable
class MagikaFormatForensicsService(Protocol):
    """Protocol for format forensics, extension mismatch auditing, and polyglot verification."""

    def audit_extension_mismatch(self, target_path: str, recursive: bool = True) -> dict[str, Any]:
        ...

    def polyglot_check(self, file_path: str, threshold: float = 0.70) -> dict[str, Any]:
        ...

    def quarantine_scan(self, file_path: str, blocked_groups: list[str] | None = None) -> dict[str, Any]:
        ...


MAGIKA_FORMAT_FORENSICS_KEY: ServiceKey[MagikaFormatForensicsService] = ServiceKey("service.magika_format_forensics")


class MagikaFormatForensicsEngine:
    """Forensic engine analyzing file discrepancies, masquerading payloads, and polyglots."""

    def __init__(self, detector: MagikaContentDetectorEngine | None = None) -> None:
        self._detector = detector or _GLOBAL_DETECTOR

    def audit_extension_mismatch(self, target_path: str, recursive: bool = True) -> dict[str, Any]:
        p = Path(target_path)
        if not p.exists():
            return {"status": "error", "error": f"Target path not found: {target_path}"}

        targets = []
        if p.is_file():
            targets = [p]
        elif p.is_dir():
            pattern = "**/*" if recursive else "*"
            targets = [f for f in p.glob(pattern) if f.is_file()]

        mismatches: list[dict[str, Any]] = []
        audited_count = 0

        for f in targets:
            audited_count += 1
            info = self._detector.identify_path(str(f))
            if info.get("status") != "ok":
                continue

            file_ext = f.suffix.lstrip(".").lower()
            valid_exts = [e.lower() for e in info.get("extensions", [])]
            detected_label = str(info.get("label", ""))
            detected_group = str(info.get("group", ""))
            score = float(info.get("score", 0.0))

            # Check if extension is mismatched with high confidence
            is_mismatch = False
            risk_level = "none"

            if file_ext and valid_exts and (file_ext not in valid_exts):
                # Critical risk: executable/script masquerading as doc/media
                if detected_group in ("executable", "code") and file_ext in ("jpg", "jpeg", "png", "gif", "pdf", "docx", "xlsx", "txt"):
                    is_mismatch = True
                    risk_level = "critical"
                elif file_ext in ("txt", "log") and detected_group not in ("text", "code"):
                    is_mismatch = True
                    risk_level = "medium"
                elif score >= 0.70 and detected_group != "unknown":
                    is_mismatch = True
                    risk_level = "low"

            if is_mismatch:
                mismatches.append({
                    "file_path": str(f),
                    "file_extension": file_ext,
                    "detected_label": detected_label,
                    "detected_mime": str(info.get("mime_type")),
                    "detected_group": detected_group,
                    "valid_extensions": valid_exts,
                    "confidence_score": score,
                    "risk_level": risk_level,
                    "is_text": bool(info.get("is_text", False)),
                })

        return {
            "status": "ok",
            "target_path": str(p),
            "audited_count": audited_count,
            "mismatches_count": len(mismatches),
            "mismatches": mismatches,
        }

    def polyglot_check(self, file_path: str, threshold: float = 0.70) -> dict[str, Any]:
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            return {"status": "error", "error": f"File not found: {file_path}"}

        info = self._detector.identify_path(str(p))
        if info.get("status") != "ok":
            return info

        score = float(info.get("score", 0.0))
        label = str(info.get("label", ""))
        file_size = p.stat().st_size

        is_polyglot_candidate = False
        indicators: list[str] = []

        try:
            with open(p, "rb") as f:
                header = f.read(1024)
                f.seek(max(0, file_size - 1024))
                footer = f.read(1024)

            # Check for ZIP header (PK) in footer or trailer
            if b"PK" in footer and not header.startswith(b"PK"):
                is_polyglot_candidate = True
                indicators.append("Appended ZIP archive structure detected in trailer bytes (Zip-Slip or Polyglot)")

            # Check for ELF / PE signature in non-executable file
            if (b"\x7fELF" in header or b"MZ" in header[:2]) and info.get("group") != "executable":
                is_polyglot_candidate = True
                indicators.append("Executable binary magic header detected in non-executable format")

            # Check for HTML/Script tags inside binary format
            if any(tag in header.lower() for tag in (b"<script", b"<html", b"<?php")) and not info.get("is_text", False):
                is_polyglot_candidate = True
                indicators.append("Executable script/HTML tags detected inside binary media container")

            # Low confidence score check
            if score < threshold:
                indicators.append(f"Model prediction confidence ({score:.3f}) below threshold ({threshold:.3f})")
                if len(indicators) > 1:
                    is_polyglot_candidate = True

        except Exception as e:
            return {"status": "error", "error": f"Failed reading file bytes: {e}"}

        return {
            "status": "ok",
            "file_path": str(p),
            "is_polyglot_candidate": is_polyglot_candidate,
            "detected_label": label,
            "confidence_score": score,
            "indicators_count": len(indicators),
            "indicators": indicators,
        }

    def quarantine_scan(self, file_path: str, blocked_groups: list[str] | None = None) -> dict[str, Any]:
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            return {"status": "error", "error": f"File not found: {file_path}"}

        blocks = [g.lower() for g in (blocked_groups or ["executable", "code"])]
        info = self._detector.identify_path(str(p))
        if info.get("status") != "ok":
            return info

        detected_group = str(info.get("group", "")).lower()
        detected_label = str(info.get("label", ""))
        score = float(info.get("score", 0.0))

        quarantined = detected_group in blocks
        violation_reason = ""
        if quarantined:
            violation_reason = f"Prohibited content group '{detected_group}' detected (label: '{detected_label}', score: {score:.3f})"

        return {
            "status": "ok",
            "file_path": str(p),
            "quarantined": quarantined,
            "detected_group": detected_group,
            "detected_label": detected_label,
            "confidence_score": score,
            "blocked_groups": blocks,
            "violation_reason": violation_reason,
        }


# Global engine singleton
_GLOBAL_FORENSICS = MagikaFormatForensicsEngine()


# -----------------------------------------------------------------------------
# Top-level Tool Functions Matching Entrypoint Signatures
# -----------------------------------------------------------------------------

def magika_audit_extension_mismatch(target_path: str, recursive: bool = True) -> dict[str, Any]:
    """Scan files to detect extension spoofing where the deep learning content type contradicts the file extension."""
    return _GLOBAL_FORENSICS.audit_extension_mismatch(target_path=target_path, recursive=recursive)


def magika_polyglot_check(file_path: str, threshold: float = 0.70) -> dict[str, Any]:
    """Inspect a file for low prediction margins, ambiguous classifications, or composite headers characteristic of polyglots."""
    return _GLOBAL_FORENSICS.polyglot_check(file_path=file_path, threshold=threshold)


def magika_quarantine_scan(file_path: str, blocked_groups: list[str] | None = None) -> dict[str, Any]:
    """Evaluate a file against an untrusted upload policy, quarantining files belonging to prohibited content groups."""
    return _GLOBAL_FORENSICS.quarantine_scan(file_path=file_path, blocked_groups=blocked_groups)


# -----------------------------------------------------------------------------
# Harness Plugin Class & IoC Lifecycle
# -----------------------------------------------------------------------------

class MagikaFormatForensicsPlugin(HarnessPlugin, MagikaFormatForensicsService):
    """Brain Harness Plugin providing Google Magika format forensics and polyglot security verification."""

    name = "plugin.magika_format_forensics"
    version = "1.0.0"
    description = "Google Magika format forensics: extension spoofing detection, polyglot binary auditing, and upload quarantine gating"
    trusted = True

    def __init__(self, engine: MagikaFormatForensicsEngine | None = None) -> None:
        self._engine = engine or _GLOBAL_FORENSICS

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [MAGIKA_FORMAT_FORENSICS_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return [MAGIKA_CONTENT_DETECTOR_KEY]

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(MAGIKA_FORMAT_FORENSICS_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # Protocol Implementation
    # -------------------------------------------------------------------------

    def audit_extension_mismatch(self, target_path: str, recursive: bool = True) -> dict[str, Any]:
        return self._engine.audit_extension_mismatch(target_path=target_path, recursive=recursive)

    def polyglot_check(self, file_path: str, threshold: float = 0.70) -> dict[str, Any]:
        return self._engine.polyglot_check(file_path=file_path, threshold=threshold)

    def quarantine_scan(self, file_path: str, blocked_groups: list[str] | None = None) -> dict[str, Any]:
        return self._engine.quarantine_scan(file_path=file_path, blocked_groups=blocked_groups)
