"""Authoritative compiler for multimodal <SHOW_FILE> and <GENERATE_FILE> tag protocols."""

from __future__ import annotations

import re
from pathlib import Path

import structlog

from harness.services.cellcog.models import (
    GENERATE_FILE_REGEX,
    MAX_ATTACHMENT_SIZE_BYTES,
    SENSITIVE_FILE_PATTERNS,
    SHOW_FILE_REGEX,
    MultimodalCompilationResult,
    infer_mime_type,
)

logger = structlog.get_logger(__name__)


class MultimodalProtocolCompiler:
    """Authoritative compiler for multimodal <SHOW_FILE> and <GENERATE_FILE> tag protocols."""

    @classmethod
    def detect_mime(cls, path_or_str: str | Path) -> str:
        """Infer MIME type from file extension or path."""
        return infer_mime_type(path_or_str)

    @classmethod
    def is_sensitive(cls, file_path: str | Path) -> bool:
        """Check if a file path matches any sensitive credential pattern."""
        path_str = str(file_path)
        return any(pattern.search(path_str) for pattern in SENSITIVE_FILE_PATTERNS)

    @classmethod
    def compile_prompt(
        cls,
        prompt: str,
        check_disk: bool = False,
        max_file_size: int = MAX_ATTACHMENT_SIZE_BYTES,
    ) -> MultimodalCompilationResult:
        """Parse, validate, and compile prompt tags into an authoritative compilation result."""
        valid_inputs: list[str] = []
        rejected_inputs: list[str] = []
        missing_files: list[str] = []
        oversized_files: list[str] = []

        # 1. Parse <SHOW_FILE> tags
        show_matches = SHOW_FILE_REGEX.findall(prompt)
        for raw in show_matches:
            clean = raw.strip()
            if not clean:
                continue

            if cls.is_sensitive(clean):
                logger.warn("multimodal_compiler_rejected_sensitive", path=clean)
                rejected_inputs.append(clean)
                continue

            p = Path(clean)
            if check_disk:
                if not p.exists():
                    missing_files.append(clean)
                    continue
                if p.is_file() and p.stat().st_size > max_file_size:
                    logger.warn("multimodal_compiler_rejected_oversized", path=clean, size=p.stat().st_size)
                    oversized_files.append(clean)
                    continue

            valid_inputs.append(clean)

        # 2. Sanitize prompt by redacting sensitive or oversized inputs
        sanitized_prompt = prompt
        for rej in rejected_inputs:
            sanitized_prompt = re.sub(
                rf"<SHOW_FILE>\s*{re.escape(rej)}\s*</SHOW_FILE>",
                f"[REDACTED_SENSITIVE_FILE: {Path(rej).name}]",
                sanitized_prompt,
                flags=re.IGNORECASE,
            )
        for over in oversized_files:
            sanitized_prompt = re.sub(
                rf"<SHOW_FILE>\s*{re.escape(over)}\s*</SHOW_FILE>",
                f"[REDACTED_OVERSIZED_FILE: {Path(over).name}]",
                sanitized_prompt,
                flags=re.IGNORECASE,
            )

        # 3. Parse <GENERATE_FILE> tags
        gen_matches = GENERATE_FILE_REGEX.findall(sanitized_prompt)
        output_destinations = tuple(m.strip() for m in gen_matches if m.strip())

        return MultimodalCompilationResult(
            sanitized_prompt=sanitized_prompt,
            valid_inputs=tuple(valid_inputs),
            rejected_inputs=tuple(rejected_inputs),
            output_destinations=output_destinations,
            missing_files=tuple(missing_files),
            oversized_files=tuple(oversized_files),
        )


def parse_show_file_tags(prompt: str) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    """Backward-compatible wrapper around MultimodalProtocolCompiler."""
    res = MultimodalProtocolCompiler.compile_prompt(prompt, check_disk=False)
    return res.sanitized_prompt, res.valid_inputs, res.rejected_inputs


def parse_generate_file_tags(prompt: str) -> tuple[str, tuple[str, ...]]:
    """Backward-compatible wrapper around MultimodalProtocolCompiler."""
    res = MultimodalProtocolCompiler.compile_prompt(prompt, check_disk=False)
    return res.sanitized_prompt, res.output_destinations
