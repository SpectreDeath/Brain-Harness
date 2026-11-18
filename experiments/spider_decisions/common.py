"""Shared bootstrap, snapshot, query, and logging helpers for spider experiments."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from typing import Any

WORKSPACE = Path(r"d:\GitHub\projects\Brain Harness")
VAULT = WORKSPACE / ".harness" / "knowledge"
EXP_DIR = WORKSPACE / "experiments" / "spider_decisions"
RESULTS = EXP_DIR / "results"
SNAPSHOTS = RESULTS / "snapshots"
GOOGLE_ROOT = Path(r"D:\GitHub\cloned\Google")
GRM_ROOT = GOOGLE_ROOT / "google-research-master"
AIRLLM_ROOT = Path(r"D:\GitHub\cloned\AIRLLM SUITE")


def bootstrap() -> None:
    """Configure UTF-8 standard streams and prepend workspace/src to sys.path."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    for candidate in (str(WORKSPACE / "src"), str(WORKSPACE)):
        if candidate not in sys.path:
            sys.path.insert(0, candidate)


def spider() -> Any:
    """Return an OntologySpiderKernelService instance."""
    bootstrap()
    from harness.services.ontology_spider import OntologySpiderKernelService

    return OntologySpiderKernelService()


def load_vault_model() -> Any:
    """Load the Brain Harness Knowledge Vault ontology model."""
    return spider().load_vault(VAULT)


def load_repo_model(
    repo_path: Path,
    snapshot_name: str,
    *,
    refresh: bool = False,
    max_depth: int = 4,
    max_files_per_unit: int | None = 60,
) -> Any:
    """Load cached JSON snapshot or build live repository ontology model and cache it."""
    bootstrap()
    from ontology_spider.api import export_model, load_model

    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    snap_path = SNAPSHOTS / f"{snapshot_name}.json"
    if snap_path.exists() and not refresh:
        return load_model(snap_path)

    model = spider().load_repository_model(
        repo_path,
        vault_dir=VAULT,
        max_depth=max_depth,
        max_files_per_unit=max_files_per_unit,
    )
    snap_path.write_text(export_model(model, format="json"), encoding="utf-8")
    return model


def query(model: Any, q: str) -> dict[str, Any]:
    """Execute a controlled .dialog query against an OntologyModel."""
    return spider().query_model(model, q)


def project_entities(model: Any) -> dict[str, Mapping[str, Any]]:
    """Return {entity_id: attributes} for entities representing project/unit nodes."""
    out: dict[str, Mapping[str, Any]] = {}
    for eid, ent in model.entities.items():
        attrs = getattr(ent, "attributes", None)
        if isinstance(attrs, Mapping) and "raw_name" in attrs:
            out[str(eid)] = attrs
    return out


def write_json(phase: int, name: str, obj: Any) -> Path:
    """Write JSON output under results/pNN/<name>.json."""
    out_dir = RESULTS / f"p{phase:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name}.json"
    out_path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    return out_path


def write_md(phase: int, name: str, text: str) -> Path:
    """Write UTF-8 Markdown output under results/pNN/<name>.md."""
    out_dir = RESULTS / f"p{phase:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name}.md"
    out_path.write_text(text, encoding="utf-8")
    return out_path


def append_log(phase: int, title: str, bullets: list[str]) -> None:
    """Append a dated section for the completed phase to RESULTS_LOG.md."""
    log_path = EXP_DIR / "RESULTS_LOG.md"
    ts = datetime.now(UTC).isoformat(timespec="seconds")
    lines = [f"\n## Phase {phase} — {title} ({ts})"]
    for item in bullets:
        cleaned = item.strip()
        if cleaned.startswith("- "):
            lines.append(cleaned)
        else:
            lines.append(f"- {cleaned}")
    lines.append("")
    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    log_path.write_text(existing + "\n".join(lines), encoding="utf-8")
