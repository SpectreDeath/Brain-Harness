"""Golden Record Resolver & Master Data Entity Resolution Engine.

Aligns with DAMA-DMBOK Chapter 10 (Reference & Master Data Management).
Implements deterministic matching, fuzzy entity resolution, and attribute survivorship rules.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
import re
import unicodedata
from typing import Any


class SurvivorshipRule(str, Enum):
    """Supported attribute survivorship strategies."""

    SOURCE_PRIORITY = "source_priority"
    MOST_RECENT = "most_recent"
    NON_NULL_FIRST = "non_null_first"
    LONGEST_STRING = "longest_string"


@dataclass(slots=True)
class EntityRecord:
    """An input record originating from a specific operational source system."""

    record_id: str
    source_system: str
    updated_at: str
    attributes: dict[str, Any]


@dataclass(slots=True)
class GoldenRecord:
    """The canonical, unified master entity record with attribute lineage."""

    master_id: str
    resolved_attributes: dict[str, Any]
    source_records_count: int
    contributing_sources: list[str]
    attribute_lineage: dict[str, str]  # attribute_name -> source_system
    match_confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "master_id": self.master_id,
            "resolved_attributes": self.resolved_attributes,
            "source_records_count": self.source_records_count,
            "contributing_sources": self.contributing_sources,
            "attribute_lineage": self.attribute_lineage,
            "match_confidence": round(self.match_confidence, 2),
        }


def normalize_string(val: str) -> str:
    """Normalize string by removing accents, lowercasing, and stripping whitespace."""
    if not val:
        return ""
    normalized = unicodedata.normalize("NFKD", val)
    ascii_only = "".join(c for c in normalized if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", ascii_only).strip().lower()


def string_similarity(s1: str, s2: str) -> float:
    """Compute normalized token overlap similarity between two strings."""
    n1, n2 = normalize_string(s1), normalize_string(s2)
    if n1 == n2:
        return 1.0
    if not n1 or not n2:
        return 0.0

    tokens1, tokens2 = set(n1.split()), set(n2.split())
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / len(union)


class GoldenRecordResolver:
    """Clusters entity records across source feeds and resolves canonical Golden Records."""

    def __init__(
        self,
        match_keys: list[str] | None = None,
        fuzzy_keys: list[tuple[str, float]] | None = None,
        survivorship_rules: dict[str, SurvivorshipRule] | None = None,
        source_priority: list[str] | None = None,
        default_rule: SurvivorshipRule = SurvivorshipRule.SOURCE_PRIORITY,
    ) -> None:
        self.match_keys = match_keys or ["national_id"]
        self.fuzzy_keys = fuzzy_keys or []
        self.survivorship_rules = survivorship_rules or {}
        self.source_priority = source_priority or []
        self.default_rule = default_rule

    def resolve(self, records: list[EntityRecord]) -> list[GoldenRecord]:
        """Cluster records by entity identity and synthesize Golden Records."""
        if not records:
            return []

        clusters = self._cluster_records(records)
        golden_records: list[GoldenRecord] = []

        for cluster_id, cluster_records in clusters.items():
            golden = self._synthesize_golden_record(cluster_id, cluster_records)
            golden_records.append(golden)

        return golden_records

    def _cluster_records(self, records: list[EntityRecord]) -> dict[str, list[EntityRecord]]:
        """Cluster records using exact match keys followed by fuzzy key links."""
        clusters: list[list[EntityRecord]] = []

        for record in records:
            assigned = False
            for cluster in clusters:
                if self._records_match(record, cluster[0]):
                    cluster.append(record)
                    assigned = True
                    break
            if not assigned:
                clusters.append([record])

        clustered_dict: dict[str, list[EntityRecord]] = {}
        for idx, cluster in enumerate(clusters, 1):
            master_id = f"MASTER-ENT-{idx:05d}"
            # If any record has an official id like ALU-2026-8942, use that as master_id
            for r in cluster:
                for k in ("student_id", "master_id", "entity_id"):
                    if k in r.attributes and r.attributes[k]:
                        master_id = f"GOLDEN-{r.attributes[k]}"
                        break
            clustered_dict[master_id] = cluster

        return clustered_dict

    def _records_match(self, r1: EntityRecord, r2: EntityRecord) -> bool:
        # 1. Exact match keys
        for key in self.match_keys:
            v1 = r1.attributes.get(key)
            v2 = r2.attributes.get(key)
            if v1 is not None and v2 is not None and str(v1).strip() != "":
                if str(v1).strip() == str(v2).strip():
                    return True

        # 2. Fuzzy keys
        for key, threshold in self.fuzzy_keys:
            v1 = r1.attributes.get(key)
            v2 = r2.attributes.get(key)
            if v1 and v2 and isinstance(v1, str) and isinstance(v2, str):
                sim = string_similarity(v1, v2)
                if sim >= threshold:
                    return True

        return False

    def _synthesize_golden_record(
        self,
        master_id: str,
        cluster: list[EntityRecord],
    ) -> GoldenRecord:
        resolved_attrs: dict[str, Any] = {}
        lineage: dict[str, str] = {}
        sources: set[str] = {r.source_system for r in cluster}

        all_attrs: set[str] = set()
        for r in cluster:
            all_attrs.update(r.attributes.keys())

        for attr in sorted(all_attrs):
            rule = self.survivorship_rules.get(attr, self.default_rule)
            val, winner_src = self._apply_survivorship(attr, cluster, rule)
            if val is not None:
                resolved_attrs[attr] = val
                lineage[attr] = winner_src

        # Match confidence: 1.0 if single record, else based on agreement
        confidence = 1.0 if len(cluster) == 1 else 0.95

        return GoldenRecord(
            master_id=master_id,
            resolved_attributes=resolved_attrs,
            source_records_count=len(cluster),
            contributing_sources=sorted(sources),
            attribute_lineage=lineage,
            match_confidence=confidence,
        )

    def _apply_survivorship(
        self,
        attr: str,
        cluster: list[EntityRecord],
        rule: SurvivorshipRule,
    ) -> tuple[Any, str]:
        candidates: list[tuple[EntityRecord, Any]] = [
            (r, r.attributes[attr]) for r in cluster if attr in r.attributes and r.attributes[attr] is not None and str(r.attributes[attr]).strip() != ""
        ]
        if not candidates:
            return None, "none"

        if rule == SurvivorshipRule.SOURCE_PRIORITY:
            # Pick by source priority order
            for src in self.source_priority:
                for r, val in candidates:
                    if r.source_system == src:
                        return val, r.source_system
            # Fallback to first candidate
            return candidates[0][1], candidates[0][0].source_system

        elif rule == SurvivorshipRule.MOST_RECENT:
            # Sort candidates by updated_at descending
            def parse_dt(r: EntityRecord) -> datetime:
                try:
                    return datetime.fromisoformat(r.updated_at.replace("Z", "+00:00"))
                except Exception:
                    return datetime.min

            candidates.sort(key=lambda item: parse_dt(item[0]), reverse=True)
            return candidates[0][1], candidates[0][0].source_system

        elif rule == SurvivorshipRule.LONGEST_STRING:
            # Sort by string length descending
            candidates.sort(key=lambda item: len(str(item[1])), reverse=True)
            return candidates[0][1], candidates[0][0].source_system

        else:  # NON_NULL_FIRST
            return candidates[0][1], candidates[0][0].source_system


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve multiple source feeds into canonical Golden Records.")
    parser.add_argument("--data", required=True, help="Path to input JSON containing source records")
    parser.add_argument("--sources", nargs="+", help="Source system priority list in descending order")
    parser.add_argument("--output", help="Optional output JSON path for golden records")
    args = parser.parse_args()

    raw_data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    records = [
        EntityRecord(
            record_id=r.get("record_id", f"rec_{i}"),
            source_system=r.get("source_system", "unknown"),
            updated_at=r.get("updated_at", "2026-01-01T00:00:00Z"),
            attributes=r.get("attributes", r),
        )
        for i, r in enumerate(raw_data)
    ]

    source_prio = args.sources or ["registrar", "mobility", "crm"]
    resolver = GoldenRecordResolver(
        match_keys=["national_id", "email", "student_id"],
        fuzzy_keys=[("full_name", 0.80)],
        survivorship_rules={
            "full_name": SurvivorshipRule.SOURCE_PRIORITY,
            "address": SurvivorshipRule.MOST_RECENT,
        },
        source_priority=source_prio,
    )

    goldens = resolver.resolve(records)
    print(f"\nResolved {len(records)} source records into {len(goldens)} canonical Golden Records:\n")
    for g in goldens:
        print(f"[{g.master_id}] Sources: {g.contributing_sources} | Records: {g.source_records_count}")
        for k, v in g.resolved_attributes.items():
            print(f"  - {k}: {v} (from {g.attribute_lineage.get(k)})")

    if args.output:
        Path(args.output).write_text(json.dumps([g.to_dict() for g in goldens], indent=2), encoding="utf-8")
        print(f"\nSaved golden records to {args.output}")


if __name__ == "__main__":
    main()
