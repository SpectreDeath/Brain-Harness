"""Knowledge Vault exporter committing dataset schemas in canonical dual-file format (Rule 40)."""

from __future__ import annotations

import datetime
import hashlib
import json
import re
from pathlib import Path

from .models import HfColumnSchema, HfDatasetMetadata, HfDatasetVaultCommit


def commit_to_vault(
    dataset_name: str,
    metadata: HfDatasetMetadata,
    schemas: list[HfColumnSchema],
    vault_root: str | None = None,
) -> HfDatasetVaultCommit:
    """Commit dataset catalog and schema provenance to Knowledge Vault (Rule 40)."""
    clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", dataset_name.lower()).strip("_")
    fingerprint = hashlib.sha256(
        f"{clean_name}:{metadata.num_rows}:{metadata.format}".encode()
    ).hexdigest()[:8]
    ki_id = f"ki_dataset_{clean_name}_{fingerprint}"

    root = Path(vault_root) if vault_root else Path(".harness/knowledge")
    ki_dir = root / ki_id
    ki_dir.mkdir(parents=True, exist_ok=True)

    meta_file = ki_dir / "metadata.json"
    summary_file = ki_dir / "summary.md"

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    metadata_payload = {
        "id": ki_id,
        "title": f"Dataset Catalog: {dataset_name}",
        "created_at": now_iso,
        "category": "data_engineering",
        "source": dataset_name,
        "dataset": {
            "name": metadata.name,
            "split": metadata.split,
            "num_rows": metadata.num_rows,
            "format": metadata.format,
            "byte_size": metadata.byte_size,
            "is_streaming": metadata.is_streaming,
        },
        "columns": [
            {
                "name": c.name,
                "arrow_type": c.arrow_type,
                "is_nullable": c.is_nullable,
                "feature_type": c.feature_type,
            }
            for c in schemas
        ],
        "cache_fingerprint": fingerprint,
    }
    meta_file.write_text(json.dumps(metadata_payload, indent=2), encoding="utf-8")

    summary_lines = [
        f"# Dataset Catalog: {dataset_name}",
        "",
        f"- **Knowledge Item ID**: `{ki_id}`",
        f"- **Dataset Split**: `{metadata.split}`",
        f"- **Total Rows**: {metadata.num_rows}",
        f"- **Storage Format**: `{metadata.format}`",
        f"- **Physical Size**: {metadata.byte_size:,} bytes",
        f"- **Streaming Mode**: `{metadata.is_streaming}`",
        f"- **Cache Fingerprint**: `{fingerprint}`",
        "",
        "## Schema Definition",
        "",
        "| Column Name | Arrow Type | Nullable | Feature Type |",
        "|---|---|---|---|",
    ]
    for col in schemas:
        summary_lines.append(
            f"| `{col.name}` | `{col.arrow_type}` | {col.is_nullable} | `{col.feature_type}` |"
        )

    summary_lines.extend(
        [
            "",
            "## Epistemic Checkpoint",
            f"Logged to Knowledge Vault at `{now_iso}` via `DefaultHfDatasetsService`.",
            "",
        ]
    )
    summary_file.write_text("\n".join(summary_lines), encoding="utf-8")

    return HfDatasetVaultCommit(
        ki_id=ki_id,
        title=metadata_payload["title"],
        summary=f"Catalogued {dataset_name} ({metadata.num_rows} rows, {len(schemas)} columns)",
        metadata_path=str(meta_file),
        summary_path=str(summary_file),
        cache_fingerprint=fingerprint,
        features_count=len(schemas),
        total_rows=metadata.num_rows,
    )
