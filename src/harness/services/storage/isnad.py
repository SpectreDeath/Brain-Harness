"""Isnad chain-of-custody verification and cryptographic hashing for knowledge items."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from harness.services.storage.models import IsnadLineageBlock, KnowledgeItemRecord


class IsnadAuditMixin:
    """Provides Isnad provenance verification and SHA-256 integrity calculation."""

    async def get_knowledge_item(self, ki_id: str) -> KnowledgeItemRecord | None:
        raise NotImplementedError

    def compute_sha256(self, content: str | bytes) -> str:
        """Compute SHA-256 hash for provenance nodes."""
        data = content.encode("utf-8") if isinstance(content, str) else content
        return hashlib.sha256(data).hexdigest()

    async def verify_isnad_integrity(self, ki_id: str, base_dir: Path | str = ".") -> dict[str, Any]:
        """Verify the Isnad lineage claims and primary source files for a given KI."""
        ki = await self.get_knowledge_item(ki_id)
        if not ki:
            return {"status": "error", "error": f"Knowledge item {ki_id} not found"}

        base = Path(base_dir).resolve()
        claims_checked: list[dict[str, Any]] = []
        all_valid = True

        isnad_data = (
            ki.isnad.model_dump()
            if isinstance(ki.isnad, IsnadLineageBlock)
            else (ki.isnad if isinstance(ki.isnad, dict) else {})
        )
        claims = isnad_data.get("claims", [])
        if not claims and "primary_source" in isnad_data:
            claims = [
                {
                    "assertion": ki.title,
                    "lineage": [{"uri": isnad_data["primary_source"], "verified": isnad_data.get("verified", False)}],
                }
            ]

        for claim in claims:
            assertion = claim.get("assertion", "")
            lineage_nodes = claim.get("lineage", [])
            node_results = []
            for node in lineage_nodes:
                uri = node.get("uri", "")
                clean_path_part = uri.replace("file:///", "").replace("file://", "").split("#")[0]
                target_file = base / clean_path_part if not Path(clean_path_part).is_absolute() else Path(clean_path_part)
                exists = target_file.exists()
                if not exists:
                    all_valid = False
                node_results.append(
                    {
                        "uri": uri,
                        "target_path": str(target_file),
                        "file_exists": exists,
                        "claimed_verified": node.get("verified", False),
                    }
                )
            claims_checked.append(
                {
                    "assertion": assertion,
                    "nodes": node_results,
                }
            )

        return {
            "status": "ok" if all_valid else "warning",
            "ki_id": ki_id,
            "title": ki.title,
            "isnad_status": isnad_data.get("status", "VERIFIED"),
            "integrity_verified": all_valid,
            "claims_audited": claims_checked,
        }
