# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pydantic",
#     "pyyaml",
# ]
# ///

"""Validation script for Paperless-NGX document ingestion readiness."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Rule 23 & Rule 50: Explicit UTF-8 stream codec
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def validate_file_readiness(file_path: str) -> dict[str, str | bool | int]:
    """Validate that target file exists, is non-empty, and has an allowed document extension."""
    path = Path(file_path)
    if not path.exists():
        return {"valid": False, "error": f"File does not exist: {file_path}"}
    if not path.is_file():
        return {"valid": False, "error": f"Path is not a regular file: {file_path}"}

    size = path.stat().st_size
    if size == 0:
        return {"valid": False, "error": f"File is empty (0 bytes): {file_path}"}

    supported_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".txt", ".docx", ".eml"}
    ext = path.suffix.lower()
    if ext not in supported_extensions:
        return {
            "valid": False,
            "error": f"Unsupported extension '{ext}'. Supported: {sorted(supported_extensions)}",
        }

    return {
        "valid": True,
        "size_bytes": size,
        "extension": ext,
        "filename": path.name,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate document ingestion readiness")
    parser.add_argument("file_path", help="Path to document file")
    args = parser.parse_args()

    report = validate_file_readiness(args.file_path)
    print(json.dumps(report, indent=2))
    if not report.get("valid"):
        sys.exit(1)


if __name__ == "__main__":
    main()
