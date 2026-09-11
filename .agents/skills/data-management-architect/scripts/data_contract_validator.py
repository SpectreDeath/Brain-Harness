"""Open Data Contract Validator — evaluates dataset payloads against machine-readable contracts.

Aligns with the Open Data Contract Standard (ODCS) and DAMA-DMBOK data integration principles.
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
class ContractViolation:
    """Represents an individual contract compliance violation."""

    record_index: int
    field: str
    violation_type: str
    message: str
    actual_value: Any

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_index": self.record_index,
            "field": self.field,
            "type": self.violation_type,
            "violation_type": self.violation_type,
            "message": self.message,
            "actual_value": str(self.actual_value),
        }


@dataclass(slots=True)
class ContractValidationReport:
    """Summary report resulting from contract validation."""

    is_compliant: bool
    contract_name: str
    version: str
    total_records: int
    valid_records: int
    quarantine_count: int
    violations: list[ContractViolation] = field(default_factory=list)

    @property
    def compliance_rate(self) -> float:
        if self.total_records == 0:
            return 100.0
        return (self.valid_records / self.total_records) * 100.0

    @property
    def quarantined_records(self) -> int:
        return self.quarantine_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_compliant": self.is_compliant,
            "contract_name": self.contract_name,
            "version": self.version,
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "quarantine_count": self.quarantine_count,
            "quarantined_records": self.quarantine_count,
            "compliance_rate": self.compliance_rate,
            "violations": [
                {
                    "record_index": v.record_index,
                    "field": v.field,
                    "type": v.violation_type,
                    "message": v.message,
                    "actual_value": str(v.actual_value),
                }
                for v in self.violations
            ],
        }


class DataContractValidator:
    """Validates record batches against an Open Data Contract definition."""

    def __init__(self, contract: dict[str, Any], reference_time: datetime | None = None) -> None:
        self.contract = contract
        self.name = contract.get("name", "unnamed_contract")
        self.version = str(contract.get("version", "1.0.0"))
        self.reference_time = reference_time
        self.schema = contract.get("schema", {})
        raw_fields = self.schema.get("fields", {})
        if isinstance(raw_fields, list):
            self.fields = {
                f.get("name", f"field_{i}"): {k: v for k, v in f.items() if k != "name"}
                for i, f in enumerate(raw_fields)
                if isinstance(f, dict)
            }
        elif isinstance(raw_fields, dict):
            self.fields = raw_fields
        else:
            self.fields = {}
        self.sla = contract.get("sla", {})

    @classmethod
    def from_dict(cls, contract_dict: dict[str, Any], reference_time: datetime | None = None) -> DataContractValidator:
        return cls(contract_dict, reference_time=reference_time)

    @classmethod
    def from_json(cls, json_path: str | Path, reference_time: datetime | None = None) -> DataContractValidator:
        path = Path(json_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(data, reference_time=reference_time)

    def validate_dataset(
        self,
        records: list[dict[str, Any]],
        max_quarantine_ratio: float = 0.05,
        reference_time: datetime | None = None,
    ) -> ContractValidationReport:
        """Validate an iterable collection of dictionary records against contract rules."""
        violations: list[ContractViolation] = []
        valid_records = 0
        quarantine_count = 0

        for idx, record in enumerate(records):
            record_violations = self._validate_record(idx, record)
            if record_violations:
                violations.extend(record_violations)
                quarantine_count += 1
            else:
                valid_records += 1

        # SLA Freshness check
        freshness_field = self.sla.get("freshness_field")
        max_latency_hours = self.sla.get("max_latency_hours")
        if freshness_field and max_latency_hours is not None and records:
            effective_ref = reference_time or self.reference_time
            freshness_violation = self._check_freshness(
                records, freshness_field, float(max_latency_hours), reference_time=effective_ref
            )
            if freshness_violation:
                violations.append(freshness_violation)

        total = len(records)
        quarantine_ratio = (quarantine_count / total) if total > 0 else 0.0
        is_compliant = len(violations) == 0 or (quarantine_ratio <= max_quarantine_ratio and not any(v.violation_type == "sla_freshness_breach" for v in violations))

        return ContractValidationReport(
            is_compliant=is_compliant,
            contract_name=self.name,
            version=self.version,
            total_records=total,
            valid_records=valid_records,
            quarantine_count=quarantine_count,
            violations=violations,
        )

    def _validate_record(self, idx: int, record: dict[str, Any]) -> list[ContractViolation]:
        violations: list[ContractViolation] = []

        for field_name, rules in self.fields.items():
            value = record.get(field_name)
            is_required = rules.get("required", True)
            is_nullable = rules.get("nullable", False)
            expected_type = rules.get("type", "string")

            # 1. Nullability & presence check
            if value is None or (isinstance(value, str) and value.strip() == ""):
                if is_required and not is_nullable:
                    violations.append(
                        ContractViolation(
                            record_index=idx,
                            field=field_name,
                            violation_type="null_violation",
                            message=f"Field '{field_name}' is required and non-nullable, but was empty or None",
                            actual_value=value,
                        )
                    )
                continue

            # 2. Type check
            if not self._check_type(value, expected_type):
                violations.append(
                    ContractViolation(
                        record_index=idx,
                        field=field_name,
                        violation_type="type_mismatch",
                        message=f"Field '{field_name}' expected type '{expected_type}', got '{type(value).__name__}'",
                        actual_value=value,
                    )
                )
                continue

            # 3. Numeric bounds
            if expected_type in ("integer", "float", "number"):
                num_val = float(value)
                if "minimum" in rules and num_val < rules["minimum"]:
                    violations.append(
                        ContractViolation(
                            record_index=idx,
                            field=field_name,
                            violation_type="range_violation",
                            message=f"Field '{field_name}' value {num_val} is below minimum {rules['minimum']}",
                            actual_value=value,
                        )
                    )
                if "maximum" in rules and num_val > rules["maximum"]:
                    violations.append(
                        ContractViolation(
                            record_index=idx,
                            field=field_name,
                            violation_type="range_violation",
                            message=f"Field '{field_name}' value {num_val} exceeds maximum {rules['maximum']}",
                            actual_value=value,
                        )
                    )

            # 4. Pattern check
            if expected_type == "string" and "pattern" in rules:
                pattern = rules["pattern"]
                if not re.match(pattern, str(value)):
                    violations.append(
                        ContractViolation(
                            record_index=idx,
                            field=field_name,
                            violation_type="pattern_mismatch",
                            message=f"Field '{field_name}' value does not match regex pattern '{pattern}'",
                            actual_value=value,
                        )
                    )

            # 5. Enum check
            if "enum" in rules and value not in rules["enum"]:
                violations.append(
                    ContractViolation(
                        record_index=idx,
                        field=field_name,
                        violation_type="enum_violation",
                        message=f"Field '{field_name}' value '{value}' not in allowed set {rules['enum']}",
                        actual_value=value,
                    )
                )

        return violations

    def _check_type(self, value: Any, expected_type: str) -> bool:
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type in ("float", "number"):
            return (isinstance(value, (int, float)) and not isinstance(value, bool))
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "date":
            if not isinstance(value, str):
                return False
            try:
                datetime.strptime(value, "%Y-%m-%d")
                return True
            except ValueError:
                return False
        elif expected_type == "timestamp":
            if not isinstance(value, str):
                return False
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
                return True
            except ValueError:
                return False
        return True

    def _check_freshness(
        self,
        records: list[dict[str, Any]],
        field_name: str,
        max_hours: float,
        reference_time: datetime | None = None,
    ) -> ContractViolation | None:
        latest_dt: datetime | None = None

        for r in records:
            val = r.get(field_name)
            if not val or not isinstance(val, str):
                continue
            try:
                dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
                if latest_dt is None or dt > latest_dt:
                    latest_dt = dt
            except Exception:
                continue

        if latest_dt is None:
            return ContractViolation(
                record_index=-1,
                field=field_name,
                violation_type="sla_freshness_breach",
                message=f"No valid timestamps found in freshness field '{field_name}'",
                actual_value=None,
            )

        now = reference_time or self.reference_time or datetime.now(timezone.utc)
        diff_hours = (now - latest_dt).total_seconds() / 3600.0
        if diff_hours > max_hours:
            return ContractViolation(
                record_index=-1,
                field=field_name,
                violation_type="sla_freshness_breach",
                message=f"Data is stale: latest timestamp {latest_dt.isoformat()} is {diff_hours:.1f} hours old (SLA: <= {max_hours} hours)",
                actual_value=latest_dt.isoformat(),
            )
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate data records against Open Data Contract.")
    parser.add_argument("--contract", required=True, help="Path to contract JSON file")
    parser.add_argument("--data", required=True, help="Path to dataset JSON file")
    parser.add_argument("--output", help="Optional path to output validation JSON report")
    args = parser.parse_args()

    validator = DataContractValidator.from_json(args.contract)
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    if isinstance(data, dict) and "records" in data:
        data = data["records"]

    report = validator.validate_dataset(data)
    out_dict = report.to_dict()

    print(f"\n--- DATA CONTRACT VALIDATION: {report.contract_name} (v{report.version}) ---")
    print(f"Compliant: {report.is_compliant} | Rate: {report.compliance_rate:.1f}% ({report.valid_records}/{report.total_records})")
    print(f"Quarantined Records: {report.quarantine_count}")
    if report.violations:
        print(f"Total Violations: {len(report.violations)}")
        for v in report.violations[:5]:
            print(f"  [Idx {v.record_index}] {v.field}: {v.message}")
        if len(report.violations) > 5:
            print(f"  ... and {len(report.violations) - 5} more.")

    if args.output:
        Path(args.output).write_text(json.dumps(out_dict, indent=2), encoding="utf-8")
        print(f"Report saved to: {args.output}")


if __name__ == "__main__":
    main()
