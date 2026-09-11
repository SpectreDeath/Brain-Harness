#!/usr/bin/env python3
"""Slotted & Frozen Epistemic Evidence Reification Engine.

Operationalizes the 7-tuple temporal evidence object and the 5-layer
relation-vs-inference boundary matrix using memory-efficient dataclasses (Rule 12).
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
import sys
from typing import Any

# Rule 23: UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


class EvidenceStatus(str, Enum):
    """Lifecycle state of an epistemic evidence claim."""
    HYPOTHESIS = "HYPOTHESIS"
    PEER_REVIEWED = "PEER_REVIEWED"
    CONTESTED = "CONTESTED"
    REFUTED = "REFUTED"
    ACCEPTED = "ACCEPTED"


class EvidenceBoundaryLayer(str, Enum):
    """The 5 discrete boundary layers separating facts from inferences."""
    PRIMARY_FACT = "PRIMARY_FACT"                    # Direct empirical observation (immutable)
    NETWORK_STRUCTURE = "NETWORK_STRUCTURE"          # Direct topological relationship
    DERIVED_HYPOTHESIS = "DERIVED_HYPOTHESIS"        # Model-generated inference (requires inferred=True)
    VERIFICATION_DATA = "VERIFICATION_DATA"          # Replication audits & test trials
    ACTIONABLE_CONCLUSION = "ACTIONABLE_CONCLUSION"  # Synthesized high-confidence policy


@dataclass(slots=True, frozen=True)
class TemporalEvidenceObject:
    """The 7-tuple temporal evidence object: <s, p, o, t, sigma, c, sigma_status>."""
    subject: str
    predicate: str
    object: str
    time: str
    source: str
    confidence: float
    status: EvidenceStatus
    boundary_layer: EvidenceBoundaryLayer = EvidenceBoundaryLayer.PRIMARY_FACT
    derived_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        assert self.subject.strip(), "subject must not be empty"
        assert self.predicate.strip(), "predicate must not be empty"
        assert self.object.strip(), "object must not be empty"
        assert self.source.strip(), "source must not be empty"
        assert 0.0 <= self.confidence <= 1.0, f"confidence must be in [0.0, 1.0], got {self.confidence}"

        # Boundary enforcement: DERIVED_HYPOTHESIS must declare inferred flag
        if self.boundary_layer == EvidenceBoundaryLayer.DERIVED_HYPOTHESIS:
            if not self.derived_metadata.get("inferred"):
                object.__setattr__(
                    self,
                    "derived_metadata",
                    {**self.derived_metadata, "inferred": True},
                )

    def to_cypher_parameters(self) -> dict[str, Any]:
        """Convert evidence object into parameterized Cypher query map."""
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "time": self.time,
            "source": self.source,
            "confidence": self.confidence,
            "status": self.status.value,
            "boundary_layer": self.boundary_layer.value,
            "inferred": self.derived_metadata.get("inferred", False),
            "metadata_json": json.dumps(self.derived_metadata),
        }

    def to_batch_row(self) -> dict[str, Any]:
        """Alias for batch UNWIND dictionary format."""
        return self.to_cypher_parameters()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TemporalEvidenceObject:
        """Instantiate TemporalEvidenceObject from dictionary with safe fallbacks."""
        status_val = data.get("status") or "HYPOTHESIS"
        if isinstance(status_val, str):
            status = EvidenceStatus(status_val.upper())
        else:
            status = EvidenceStatus.HYPOTHESIS

        layer_val = data.get("boundary_layer") or "PRIMARY_FACT"
        if isinstance(layer_val, str):
            layer = EvidenceBoundaryLayer(layer_val.upper())
        else:
            layer = EvidenceBoundaryLayer.PRIMARY_FACT

        time_val = data.get("time") or datetime.now(timezone.utc).isoformat()

        return cls(
            subject=str(data["subject"]).strip(),
            predicate=str(data["predicate"]).strip(),
            object=str(data["object"]).strip(),
            time=str(time_val),
            source=str(data.get("source") or "unspecified"),
            confidence=float(data.get("confidence", 1.0)),
            status=status,
            boundary_layer=layer,
            derived_metadata=data.get("derived_metadata") or {},
        )


@dataclass(slots=True, frozen=True)
class EvidenceBatch:
    """Slotted, immutable collection of temporal evidence objects for bulk ingestion."""
    items: list[TemporalEvidenceObject] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.items)

    def to_unwind_batch(self) -> list[dict[str, Any]]:
        """Serialize batch for Neo4j UNWIND $batch statement."""
        return [item.to_batch_row() for item in self.items]

    @classmethod
    def from_json_list(cls, data: list[dict[str, Any]]) -> EvidenceBatch:
        """Parse list of raw dictionaries into validated EvidenceBatch."""
        items = [TemporalEvidenceObject.from_dict(row) for row in data]
        return cls(items=items)


def main() -> None:
    parser = argparse.ArgumentParser(description="Slotted Temporal Evidence Object Validator")
    parser.add_argument("--validate", "-v", type=str, help="Path to JSON file containing evidence objects")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    args = parser.parse_args()

    if not args.validate:
        parser.print_help()
        sys.exit(1)

    file_path = Path(args.validate)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    raw_data = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(raw_data, list):
        raw_data = [raw_data]

    batch = EvidenceBatch.from_json_list(raw_data)

    if args.format == "json":
        print(json.dumps({"valid_count": batch.count, "rows": batch.to_unwind_batch()}, indent=2))
    else:
        print(f"✓ Validated {batch.count} Temporal Evidence Object(s) successfully.")
        for idx, item in enumerate(batch.items, start=1):
            print(f"  [{idx}] {item.subject} -[:{item.predicate}]-> {item.object} (conf: {item.confidence}, status: {item.status.value}, layer: {item.boundary_layer.value})")


if __name__ == "__main__":
    main()
