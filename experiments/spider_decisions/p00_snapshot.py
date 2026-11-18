"""Phase 0.4: Build/refresh all 7 baseline ontology snapshots and write manifest."""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import (  # noqa: E402
    AIRLLM_ROOT,
    GOOGLE_ROOT,
    GRM_ROOT,
    SNAPSHOTS,
    WORKSPACE,
    bootstrap,
    load_repo_model,
    load_vault_model,
    write_json,
)

bootstrap()

SNAPSHOT_TARGETS: dict[str, Path | None] = {
    "vault": None,
    "google_portfolio_root": GOOGLE_ROOT,
    "grm": GRM_ROOT,
    "gvisor": GOOGLE_ROOT / "gvisor",
    "airllm": AIRLLM_ROOT / "airllm",
    "airllm_plus": AIRLLM_ROOT / "airllm-plus",
    "brain_harness_src": WORKSPACE / "src" / "harness",
}


def build_vault_snapshot() -> Any:
    """Build and export the vault ontology snapshot to results/snapshots/vault.json."""
    from ontology_spider.api import export_model

    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    model = load_vault_model()
    snap_path = SNAPSHOTS / "vault.json"
    snap_path.write_text(export_model(model, format="json"), encoding="utf-8")
    return model


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    manifest: dict[str, dict[str, Any]] = {}
    for name, target_path in SNAPSHOT_TARGETS.items():
        if name == "vault":
            model = build_vault_snapshot()
        else:
            assert target_path is not None
            model = load_repo_model(target_path, name, refresh=True)
        snap_path = SNAPSHOTS / f"{name}.json"
        ent_count = len(model.entities)
        asrt_count = len(model.assertions)
        size_bytes = snap_path.stat().st_size
        digest = _sha256(snap_path)
        manifest[name] = {
            "source_path": str(target_path) if target_path is not None else "vault",
            "snapshot_file": str(snap_path),
            "entities": ent_count,
            "assertions": asrt_count,
            "file_size_bytes": size_bytes,
            "sha256": digest,
        }
        print(f"{name}: entities={ent_count}, assertions={asrt_count}, bytes={size_bytes}")

    out = write_json(0, "snapshot_manifest", manifest)
    print(f"Wrote manifest: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
