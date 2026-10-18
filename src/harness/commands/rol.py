"""Reconstruction Obligation Ledger (ROL) CLI Commands.

Provides headless Click CLI inspection, ingestion, FSM transitions,
and cryptographic closure verification for reverse-engineered software surfaces.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import click

from harness.services.reconstruction_obligation import (
    CanonicalEvidence,
    FacetAvailability,
    ObligationItem,
    ReconstructionProof,
    StandardReconstructionObligationService,
    VALID_CASE_KINDS,
    VALID_DISPOSITIONS,
    VALID_LAYERS,
)

DEFAULT_LEDGER_PATH = Path(".harness/reconstruction_ledger.json")


def _load_service_from_ledger(ledger_path: Path) -> StandardReconstructionObligationService:
    service = StandardReconstructionObligationService()
    if not ledger_path.exists():
        return service

    try:
        data = json.loads(ledger_path.read_text(encoding="utf-8"))
        service.load_from_dict(data)
    except Exception as exc:
        click.echo(f"Warning: Failed to load existing ledger from {ledger_path}: {exc}", err=True)

    return service



def _save_service_to_ledger(service: StandardReconstructionObligationService, ledger_path: Path) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    payload = service.export_certificate()
    ledger_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


@click.group("rol")
def rol_group() -> None:
    """Reconstruction Obligation Ledger — Software reverse-engineering evidence and verification proof system."""


@rol_group.command("ingest")
@click.argument("evidence_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--ledger", type=click.Path(dir_okay=False, path_type=Path), default=DEFAULT_LEDGER_PATH, help="Path to ledger state file")
@click.option("--provider", default="generic", help="Provider ID (e.g. ghidra, rizin, wakaru)")
@click.option("--format", "subject_format", default="json", help="Subject format (e.g. elf, pe, wasm, json)")
def rol_ingest_cmd(evidence_file: Path, ledger: Path, provider: str, subject_format: str) -> None:
    """Ingest observation, compute canonical SHA-256 digest, and save CanonicalEvidence record."""
    service = _load_service_from_ledger(ledger)
    raw_content = evidence_file.read_text(encoding="utf-8")
    try:
        normalized_data = json.loads(raw_content)
    except Exception:
        normalized_data = {"raw_text": raw_content}

    record = service.ingest_evidence(
        provider_id=provider,
        subject_format=subject_format,
        normalized_result=normalized_data,
        raw_result=raw_content[:2000] if len(raw_content) > 2000 else raw_content,
    )
    _save_service_to_ledger(service, ledger)
    click.echo(record.evidence_id)


@rol_group.group("obligation")
def obligation_group() -> None:
    """Manage obligations in the ledger."""


@obligation_group.command("add")
@click.argument("description")
@click.option("--id", "obligation_id", default=None, help="Explicit obligation ID (auto-generated if omitted)")
@click.option("--layer", type=click.Choice(sorted(VALID_LAYERS)), default="application", help="System architecture layer")
@click.option("--kind", type=click.Choice(sorted(VALID_CASE_KINDS)), default="positive", help="Case kind")
@click.option("--ledger", type=click.Path(dir_okay=False, path_type=Path), default=DEFAULT_LEDGER_PATH, help="Path to ledger state file")
def rol_obligation_add_cmd(description: str, obligation_id: str | None, layer: str, kind: str, ledger: Path) -> None:
    """Register a new behavioral obligation with unowned disposition."""
    service = _load_service_from_ledger(ledger)
    oid = obligation_id or f"ob_{layer}_{len(service._obligations) + 1:04d}"
    item = service.add_obligation(
        obligation_id=oid,
        layer=layer,
        case_kind=kind,
        description=description,
        disposition="unowned",
    )
    _save_service_to_ledger(service, ledger)
    click.echo(f"Registered obligation '{item.obligation_id}' [layer: {item.layer}, disposition: {item.disposition}]")


@obligation_group.command("transition")
@click.argument("obligation_id")
@click.option("--to", "target_disposition", type=click.Choice(sorted(VALID_DISPOSITIONS)), required=True, help="Target disposition")
@click.option("--evidence", "evidence_ids", multiple=True, help="Evidence ID(s) to attach")
@click.option("--owner-path", default=None, help="Owner path for implemented obligations")
@click.option("--owner-sha256", default=None, help="Owner SHA-256 for implemented obligations")
@click.option("--ledger", type=click.Path(dir_okay=False, path_type=Path), default=DEFAULT_LEDGER_PATH, help="Path to ledger state file")
def rol_obligation_transition_cmd(
    obligation_id: str,
    target_disposition: str,
    evidence_ids: tuple[str, ...],
    owner_path: str | None,
    owner_sha256: str | None,
    ledger: Path,
) -> None:
    """Transition an obligation along the valid 8-state FSM."""
    service = _load_service_from_ledger(ledger)
    item = service.transition_disposition(
        obligation_id=obligation_id,
        new_disposition=target_disposition,
        evidence_ids=list(evidence_ids) if evidence_ids else None,
        owner_path=owner_path,
        owner_sha256=owner_sha256,
    )
    _save_service_to_ledger(service, ledger)
    click.echo(f"Transitioned '{item.obligation_id}' to '{item.disposition}'")


@rol_group.command("verify")
@click.argument("ledger_file", type=click.Path(dir_okay=False, path_type=Path), default=DEFAULT_LEDGER_PATH, required=False)
@click.option("--strict", is_flag=True, help="Exit non-zero if ledger is not fully closed")
@click.option("--json-output", is_flag=True, help="Output results in JSON format")
def rol_verify_cmd(ledger_file: Path, strict: bool, json_output: bool) -> None:
    """Compute ReconstructionProof closure digest and emit tabular audit."""
    service = _load_service_from_ledger(ledger_file)
    try:
        proof = service.verify_ledger(strict=strict)
    except ValueError as exc:
        if json_output:
            click.echo(json.dumps({"error": str(exc), "is_closed": False}, indent=2))
        else:
            click.echo(f"Verification FAILED: {exc}", err=True)
        sys.exit(1)

    if json_output:
        click.echo(json.dumps({
            "closure_digest": proof.closure_digest,
            "is_closed": proof.is_closed,
            "total_obligations": proof.total_obligations,
            "verified_count": proof.verified_count,
            "unowned_count": proof.unowned_count,
            "contradicted_count": proof.contradicted_count,
        }, indent=2))
        return

    click.echo("=" * 68)
    click.echo(" Reconstruction Obligation Ledger — Cryptographic Closure Audit")
    click.echo("=" * 68)
    click.echo(f" Ledger Source      : {ledger_file}")
    click.echo(f" Closure Digest     : {proof.closure_digest}")
    click.echo(f" Status             : {'CLOSED (SEALED)' if proof.is_closed else 'OPEN (IN PROGRESS)'}")
    click.echo(f" Total Obligations  : {proof.total_obligations}")
    click.echo(f" Verified Surfaces  : {proof.verified_count}")
    click.echo(f" Unowned Surfaces   : {proof.unowned_count}")
    click.echo(f" Contradicted       : {proof.contradicted_count}")
    click.echo("-" * 68)


@rol_group.command("export")
@click.argument("ledger_file", type=click.Path(dir_okay=False, path_type=Path), default=DEFAULT_LEDGER_PATH, required=False)
def rol_export_cmd(ledger_file: Path) -> None:
    """Emit machine-parseable JSON reconstruction certificate."""
    service = _load_service_from_ledger(ledger_file)
    cert = service.export_certificate()
    click.echo(json.dumps(cert, indent=2, ensure_ascii=False))
