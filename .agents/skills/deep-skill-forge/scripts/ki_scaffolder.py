# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""Knowledge Item Scaffolder for Knowledge Vault (Rule 40).

Authoritative dual-file generator enforcing Rule 40:
All persisted knowledge items written to disk under .harness/knowledge/<ki_id>/
must strictly adhere to the canonical dual-file directory format:
- metadata.json: Schema, title, source isnad attribution, SHA-256, claims list
- summary.md: Epistemic mental models, architecture heuristics, anti-patterns

Usage:
    python ki_scaffolder.py --id <ki_id> --title <title> --source <file> [--out-dir <dir>]
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


@dataclass(slots=True, frozen=True)
class IsnadClaim:
    """A single verifiable epistemic claim extracted from primary literature."""

    claim_id: str
    assertion: str
    evidence_quote: str
    line_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "assertion": self.assertion,
            "evidence_quote": self.evidence_quote,
            "line_number": self.line_number,
        }


@dataclass(slots=True, frozen=True)
class KnowledgeItemMetadata:
    """Immutable schema for metadata.json in Knowledge Vault dual-file format."""

    id: str
    title: str
    source_uri: str
    sha256: str
    created_at: str
    category: str
    claims: tuple[IsnadClaim, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "source_uri": self.source_uri,
            "sha256": self.sha256,
            "created_at": self.created_at,
            "category": self.category,
            "claims": [c.to_dict() for c in self.claims],
        }


class KnowledgeItemScaffolder:
    """Creates compliant dual-file directory entries under .harness/knowledge/."""

    def __init__(self, vault_root: Path | str = ".harness/knowledge") -> None:
        self.vault_root = Path(vault_root).resolve()

    def compute_sha256(self, content: str) -> str:
        """Compute SHA-256 digest of primary source text for isnad lineage."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def scaffold(
        self,
        ki_id: str,
        title: str,
        source_path: Path | str,
        category: str = "agent-architecture",
        claims: list[IsnadClaim] | None = None,
        summary_markdown: str = "",
    ) -> Path:
        """Scaffold canonical dual-file directory under .harness/knowledge/<ki_id>/."""
        clean_id = ki_id.strip().lower().replace("-", "_")
        target_dir = self.vault_root / clean_id
        target_dir.mkdir(parents=True, exist_ok=True)

        source_p = Path(source_path).resolve()
        source_text = source_p.read_text(encoding="utf-8", errors="ignore") if source_p.exists() else ""
        digest = self.compute_sha256(source_text)

        now_iso = datetime.now(timezone.utc).isoformat()
        claims_tuple = tuple(claims) if claims else ()

        meta = KnowledgeItemMetadata(
            id=clean_id,
            title=title,
            source_uri=str(source_p),
            sha256=digest,
            created_at=now_iso,
            category=category,
            claims=claims_tuple,
        )

        # 1. metadata.json
        meta_file = target_dir / "metadata.json"
        meta_file.write_text(json.dumps(meta.to_dict(), indent=2), encoding="utf-8")

        # 2. summary.md
        summary_file = target_dir / "summary.md"
        content_md = summary_markdown or (
            f"# {title}\n\n"
            f"- **Knowledge Item ID**: `{clean_id}`\n"
            f"- **Category**: `{category}`\n"
            f"- **Source**: `{source_p}`\n"
            f"- **SHA-256**: `{digest}`\n\n"
            f"## Synthesized Architectural Heuristics\n\n"
            f"Ground-truth mental models and decision heuristics distilled via `deep-skill-forge`.\n"
        )
        summary_file.write_text(content_md, encoding="utf-8")

        return target_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Knowledge Item Scaffolder (Rule 40)")
    parser.add_argument("--id", required=True, help="Knowledge Item ID (e.g. ki_context_management)")
    parser.add_argument("--title", required=True, help="Knowledge Item Title")
    parser.add_argument("--source", required=True, help="Path to primary source literature")
    parser.add_argument("--category", default="agent-architecture", help="Domain category")
    parser.add_argument("--vault-root", default=".harness/knowledge", help="Vault root directory")
    args = parser.parse_args()

    scaffolder = KnowledgeItemScaffolder(vault_root=args.vault_root)
    out_dir = scaffolder.scaffold(
        ki_id=args.id,
        title=args.title,
        source_path=args.source,
        category=args.category,
    )
    print(f"[SUCCESS] Scaffolded Knowledge Item dual-file at: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
