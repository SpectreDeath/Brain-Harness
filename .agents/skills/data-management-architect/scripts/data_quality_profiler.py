"""Data Quality Profiler & Evaluator — scores datasets across the 6 DAMA quality dimensions.

Aligns with DAMA-DMBOK Chapter 13 (Data Quality Management).
Evaluates: Accuracy, Completeness, Consistency, Timeliness, Validity, and Uniqueness.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any


@dataclass(slots=True)
class DimensionScore:
    """Individual score and metrics for one quality dimension."""

    name: str
    score: float  # 0.0 to 100.0
    passed: bool
    threshold: float
    total_checks: int
    failed_checks: int
    details: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 2),
            "passed": self.passed,
            "threshold": self.threshold,
            "total_checks": self.total_checks,
            "failed_checks": self.failed_checks,
            "details": self.details[:5],
        }


@dataclass(slots=True)
class ColumnProfile:
    """Statistical profile of a single column."""

    name: str
    total_count: int
    null_count: int
    null_percentage: float
    distinct_count: int
    inferred_type: str
    min_value: Any = None
    max_value: Any = None


@dataclass(slots=True)
class QualityScorecard:
    """Overall quality scorecard summarizing profiling and 6-dimension scoring."""

    dataset_name: str
    total_rows: int
    overall_score: float
    passed: bool
    dimensions: dict[str, DimensionScore]
    column_profiles: dict[str, ColumnProfile]

    @property
    def total_records(self) -> int:
        return self.total_rows

    @property
    def defects_summary(self) -> dict[str, int]:
        return {dim: d.failed_checks for dim, d in self.dimensions.items()}

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "total_rows": self.total_rows,
            "overall_score": round(self.overall_score, 2),
            "passed": self.passed,
            "dimensions": {
                dim_name: {
                    "score": round(d.score, 2),
                    "passed": d.passed,
                    "threshold": d.threshold,
                    "total_checks": d.total_checks,
                    "failed_checks": d.failed_checks,
                    "details": d.details[:5],
                }
                for dim_name, d in self.dimensions.items()
            },
            "columns": {
                col_name: {
                    "null_count": c.null_count,
                    "null_percentage": round(c.null_percentage, 2),
                    "distinct_count": c.distinct_count,
                    "type": c.inferred_type,
                    "min": c.min_value,
                    "max": c.max_value,
                }
                for col_name, c in self.column_profiles.items()
            },
        }

    def generate_markdown(self) -> str:
        status_badge = "PASSED" if self.passed else "FAILED"
        lines = [
            f"# Data Quality Scorecard: {self.dataset_name}",
            f"**Status**: {status_badge} | **Overall Score**: {self.overall_score:.1f}/100 | **Total Records**: {self.total_rows}",
            "",
            "## 6 DAMA Quality Dimensions",
            "| Dimension | Score | Threshold | Status | Defect Count |",
            "|---|---|---|---|---|",
        ]
        for name, dim in sorted(self.dimensions.items()):
            dim_status = "PASS" if dim.passed else "FAIL"
            lines.append(f"| {name.capitalize()} | {dim.score:.1f}% | {dim.threshold:.1f}% | {dim_status} | {dim.failed_checks} / {dim.total_checks} |")

        lines.extend([
            "",
            "## Column Profiles",
            "| Column | Type | Nulls (%) | Distinct | Min | Max |",
            "|---|---|---|---|---|---|",
        ])
        for name, col in sorted(self.column_profiles.items()):
            min_str = str(col.min_value) if col.min_value is not None else "-"
            max_str = str(col.max_value) if col.max_value is not None else "-"
            lines.append(f"| `{name}` | {col.inferred_type} | {col.null_count} ({col.null_percentage:.1f}%) | {col.distinct_count} | {min_str} | {max_str} |")

        return "\n".join(lines)


class DataQualityProfiler:
    """Profiles datasets and computes 6-dimension DAMA data quality scores."""

    def __init__(
        self,
        key_fields: list[str] | None = None,
        required_fields: list[str] | None = None,
        validation_rules: dict[str, Any] | None = None,
        consistency_rules: list[dict[str, Any]] | None = None,
        accuracy_ranges: dict[str, tuple[float, float]] | None = None,
        timeliness_field: str | None = None,
        max_latency_hours: float = 24.0,
        pass_threshold: float = 95.0,
        reference_time: datetime | None = None,
    ) -> None:
        self.key_fields = key_fields or ["id"]
        self.required_fields = required_fields or []
        self.validation_rules = validation_rules or {}
        self.consistency_rules = consistency_rules or []
        self.accuracy_ranges = accuracy_ranges or {}
        self.timeliness_field = timeliness_field
        self.max_latency_hours = max_latency_hours
        self.pass_threshold = pass_threshold
        self.reference_time = reference_time

    def profile(
        self,
        records: list[dict[str, Any]],
        dataset_name: str = "dataset",
        reference_time: datetime | None = None,
    ) -> QualityScorecard:
        """Profile dataset records and generate comprehensive QualityScorecard."""
        total_rows = len(records)
        if total_rows == 0:
            return QualityScorecard(
                dataset_name=dataset_name,
                total_rows=0,
                overall_score=100.0,
                passed=True,
                dimensions={},
                column_profiles={},
            )

        # 1. Profile columns
        col_profiles = self._profile_columns(records)

        # 2. Score the 6 dimensions
        dim_scores: dict[str, DimensionScore] = {}

        # Dimension 1: Completeness
        dim_scores["completeness"] = self._eval_completeness(records, col_profiles)

        # Dimension 2: Uniqueness
        dim_scores["uniqueness"] = self._eval_uniqueness(records)

        # Dimension 3: Validity
        dim_scores["validity"] = self._eval_validity(records)

        # Dimension 4: Accuracy
        dim_scores["accuracy"] = self._eval_accuracy(records)

        # Dimension 5: Consistency
        dim_scores["consistency"] = self._eval_consistency(records)

        # Dimension 6: Timeliness
        dim_scores["timeliness"] = self._eval_timeliness(records, reference_time=reference_time)

        # Overall composite score (unweighted mean of the 6 dimensions)
        overall = sum(d.score for d in dim_scores.values()) / len(dim_scores)
        all_passed = overall >= self.pass_threshold and all(d.passed for d in dim_scores.values())

        return QualityScorecard(
            dataset_name=dataset_name,
            total_rows=total_rows,
            overall_score=overall,
            passed=all_passed,
            dimensions=dim_scores,
            column_profiles=col_profiles,
        )

    def _profile_columns(self, records: list[dict[str, Any]]) -> dict[str, ColumnProfile]:
        total = len(records)
        all_cols: set[str] = set()
        for r in records:
            all_cols.update(r.keys())

        profiles: dict[str, ColumnProfile] = {}
        for col in sorted(all_cols):
            null_count = 0
            distinct_vals: set[str] = set()
            numeric_vals: list[float] = []
            non_null_types: set[str] = set()

            for r in records:
                val = r.get(col)
                if val is None or (isinstance(val, str) and val.strip() == ""):
                    null_count += 1
                else:
                    non_null_types.add(type(val).__name__)
                    distinct_vals.add(str(val))
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        numeric_vals.append(float(val))

            inferred = non_null_types.pop() if len(non_null_types) == 1 else ("mixed" if non_null_types else "null")
            min_val = min(numeric_vals) if numeric_vals else None
            max_val = max(numeric_vals) if numeric_vals else None

            profiles[col] = ColumnProfile(
                name=col,
                total_count=total,
                null_count=null_count,
                null_percentage=(null_count / total) * 100.0,
                distinct_count=len(distinct_vals),
                inferred_type=inferred,
                min_value=min_val,
                max_value=max_val,
            )
        return profiles

    def _eval_completeness(
        self,
        records: list[dict[str, Any]],
        profiles: dict[str, ColumnProfile],
    ) -> DimensionScore:
        req_fields = self.required_fields or list(profiles.keys())
        total_cells = len(req_fields) * len(records)
        if total_cells == 0:
            return DimensionScore("completeness", 100.0, True, 95.0, 0, 0)

        missing_cells = 0
        details: list[str] = []
        for f in req_fields:
            p = profiles.get(f)
            if p:
                missing_cells += p.null_count
                if p.null_count > 0:
                    details.append(f"Field '{f}' has {p.null_count} nulls ({p.null_percentage:.1f}%)")

        score = max(0.0, ((total_cells - missing_cells) / total_cells) * 100.0)
        return DimensionScore("completeness", score, score >= 95.0, 95.0, total_cells, missing_cells, details)

    def _eval_uniqueness(self, records: list[dict[str, Any]]) -> DimensionScore:
        total = len(records)
        if total == 0:
            return DimensionScore("uniqueness", 100.0, True, 100.0, 0, 0)

        seen_keys: set[str] = set()
        duplicates = 0
        for r in records:
            composite_key = "|".join(str(r.get(k, "")) for k in self.key_fields)
            if composite_key in seen_keys:
                duplicates += 1
            else:
                seen_keys.add(composite_key)

        score = max(0.0, ((total - duplicates) / total) * 100.0)
        details = [f"Found {duplicates} duplicate records across key fields {self.key_fields}"] if duplicates > 0 else []
        return DimensionScore("uniqueness", score, score >= 100.0, 100.0, total, duplicates, details)

    def _eval_validity(self, records: list[dict[str, Any]]) -> DimensionScore:
        if not self.validation_rules:
            return DimensionScore("validity", 100.0, True, 95.0, len(records), 0)

        total_checks = len(self.validation_rules) * len(records)
        failed_checks = 0
        details: list[str] = []

        for f, rule in self.validation_rules.items():
            pattern = rule.get("pattern")
            allowed_set = set(rule.get("enum", [])) if "enum" in rule else None

            for idx, r in enumerate(records):
                val = r.get(f)
                if val is None:
                    continue

                if pattern and not re.match(pattern, str(val)):
                    failed_checks += 1
                    if len(details) < 5:
                        details.append(f"Row {idx}: '{f}'='{val}' failed pattern {pattern}")

                if allowed_set is not None and val not in allowed_set:
                    failed_checks += 1
                    if len(details) < 5:
                        details.append(f"Row {idx}: '{f}'='{val}' not in allowed set")

        score = max(0.0, ((total_checks - failed_checks) / total_checks) * 100.0) if total_checks > 0 else 100.0
        return DimensionScore("validity", score, score >= 95.0, 95.0, total_checks, failed_checks, details)

    def _eval_accuracy(self, records: list[dict[str, Any]]) -> DimensionScore:
        if not self.accuracy_ranges:
            return DimensionScore("accuracy", 100.0, True, 95.0, len(records), 0)

        total_checks = len(self.accuracy_ranges) * len(records)
        failed_checks = 0
        details: list[str] = []

        for f, (min_v, max_v) in self.accuracy_ranges.items():
            for idx, r in enumerate(records):
                val = r.get(f)
                if val is not None and isinstance(val, (int, float)) and not isinstance(val, bool):
                    if val < min_v or val > max_v:
                        failed_checks += 1
                        if len(details) < 5:
                            details.append(f"Row {idx}: '{f}'={val} out of realistic bounds [{min_v}, {max_v}]")

        score = max(0.0, ((total_checks - failed_checks) / total_checks) * 100.0) if total_checks > 0 else 100.0
        return DimensionScore("accuracy", score, score >= 95.0, 95.0, total_checks, failed_checks, details)

    def _eval_consistency(self, records: list[dict[str, Any]]) -> DimensionScore:
        if not self.consistency_rules:
            return DimensionScore("consistency", 100.0, True, 95.0, len(records), 0)

        total_checks = len(self.consistency_rules) * len(records)
        failed_checks = 0
        details: list[str] = []

        for rule in self.consistency_rules:
            if_field = rule.get("if_field")
            if_val = rule.get("if_value")
            then_field = rule.get("then_field")
            must_not_be_null = rule.get("must_not_be_null", False)

            for idx, r in enumerate(records):
                if r.get(if_field) == if_val:
                    target_val = r.get(then_field)
                    if must_not_be_null and (target_val is None or str(target_val).strip() == ""):
                        failed_checks += 1
                        if len(details) < 5:
                            details.append(f"Row {idx}: '{if_field}'='{if_val}' requires non-null '{then_field}'")

        score = max(0.0, ((total_checks - failed_checks) / total_checks) * 100.0) if total_checks > 0 else 100.0
        return DimensionScore("consistency", score, score >= 95.0, 95.0, total_checks, failed_checks, details)

    def _eval_timeliness(
        self,
        records: list[dict[str, Any]],
        reference_time: datetime | None = None,
    ) -> DimensionScore:
        if not self.timeliness_field:
            return DimensionScore("timeliness", 100.0, True, 95.0, len(records), 0)

        now = reference_time or self.reference_time or datetime.now(timezone.utc)
        total = len(records)
        stale_count = 0
        details: list[str] = []

        for idx, r in enumerate(records):
            val = r.get(self.timeliness_field)
            if val and isinstance(val, str):
                try:
                    dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
                    age_hours = (now - dt).total_seconds() / 3600.0
                    if age_hours > self.max_latency_hours:
                        stale_count += 1
                        if len(details) < 5:
                            details.append(f"Row {idx}: timestamp {val} is {age_hours:.1f}h old (> {self.max_latency_hours}h)")
                except Exception:
                    stale_count += 1

        score = max(0.0, ((total - stale_count) / total) * 100.0) if total > 0 else 100.0
        return DimensionScore("timeliness", score, score >= 95.0, 95.0, total, stale_count, details)


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile dataset across 6 DAMA quality dimensions.")
    parser.add_argument("--data", required=True, help="Path to input dataset JSON file")
    parser.add_argument("--key", default="id", help="Primary key field for uniqueness check")
    parser.add_argument("--output", help="Optional output JSON path")
    parser.add_argument("--markdown", help="Optional output Markdown path")
    args = parser.parse_args()

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    if isinstance(data, dict) and "records" in data:
        data = data["records"]

    profiler = DataQualityProfiler(key_fields=[args.key])
    scorecard = profiler.profile(data, dataset_name=Path(args.data).stem)

    print(scorecard.generate_markdown())

    if args.output:
        Path(args.output).write_text(json.dumps(scorecard.to_dict(), indent=2), encoding="utf-8")
        print(f"\nJSON scorecard saved to {args.output}")
    if args.markdown:
        Path(args.markdown).write_text(scorecard.generate_markdown(), encoding="utf-8")
        print(f"Markdown report saved to {args.markdown}")


if __name__ == "__main__":
    main()
