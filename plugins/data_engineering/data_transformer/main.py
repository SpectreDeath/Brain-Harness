from __future__ import annotations

import csv
import io
import json
from typing import Any

import tomllib


def _parse_content(content: str, fmt: str) -> Any:
    """Parse text content according to input format."""
    f = fmt.lower().strip()
    if f == "json":
        return json.loads(content)
    elif f == "csv":
        reader = csv.DictReader(io.StringIO(content.strip()))
        return list(reader)
    elif f == "toml":
        return tomllib.loads(content)
    else:
        raise ValueError(f"Unsupported source format: '{fmt}'. Supported: json, csv, toml.")


def _serialize_content(data: Any, fmt: str) -> str:
    """Serialize parsed object to target format."""
    f = fmt.lower().strip()
    if f == "json":
        return json.dumps(data, indent=2)
    elif f == "csv":
        if not isinstance(data, list) or not data:
            raise ValueError("CSV serialization requires a non-empty list of dictionary records.")
        output = io.StringIO()
        headers = list(data[0].keys())
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        return output.getvalue().strip()
    elif f == "toml":
        if not isinstance(data, dict):
            raise ValueError("TOML serialization requires a top-level dictionary.")
        # Basic TOML key-value dumper
        lines: list[str] = []
        for k, v in data.items():
            if isinstance(v, (str, int, float, bool, list)):
                val_str = json.dumps(v)
                lines.append(f"{k} = {val_str}")
            elif isinstance(v, dict):
                lines.append(f"\n[{k}]")
                for sub_k, sub_v in v.items():
                    lines.append(f"{sub_k} = {json.dumps(sub_v)}")
        return "\n".join(lines).strip()
    else:
        raise ValueError(f"Unsupported target format: '{fmt}'. Supported: json, csv, toml.")


def data_convert_format(content: str, from_format: str, to_format: str) -> dict[str, Any]:
    """Convert structured data between JSON, CSV, and TOML."""
    try:
        parsed = _parse_content(content, from_format)
        converted = _serialize_content(parsed, to_format)
        return {
            "status": "ok",
            "from_format": from_format.lower(),
            "to_format": to_format.lower(),
            "converted_content": converted,
        }
    except Exception as e:
        return {"status": "error", "error": f"Format conversion failed: {e!s}"}


def data_filter_table(
    records: list[dict[str, Any]],
    filters: dict[str, Any] | None = None,
    sort_by: str | None = None,
    descending: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    """Filter, sort, and slice tabular records."""
    try:
        results = list(records)

        # Apply filters
        if filters:
            for k, expected in filters.items():
                results = [r for r in results if r.get(k) == expected]

        # Apply sorting
        if sort_by:
            results.sort(key=lambda r: (r.get(sort_by) is None, r.get(sort_by)), reverse=descending)

        # Apply limit
        if limit is not None and limit > 0:
            results = results[:limit]

        return {
            "status": "ok",
            "total_input_records": len(records),
            "matched_records_count": len(results),
            "records": results,
        }
    except Exception as e:
        return {"status": "error", "error": f"Table filtering failed: {e!s}"}


def data_summarize_stats(
    records: list[dict[str, Any]],
    columns: list[str] | None = None,
) -> dict[str, Any]:
    """Compute statistical summaries for table columns."""
    try:
        if not records:
            return {"status": "ok", "records_count": 0, "columns": {}}

        all_cols = columns or list(records[0].keys())
        summary: dict[str, Any] = {}

        for col in all_cols:
            values = [r.get(col) for r in records if r.get(col) is not None]
            null_count = len(records) - len(values)
            unique_count = len({str(v) for v in values})

            # Check if column is numeric
            num_values: list[float] = []
            for v in values:
                try:
                    num_values.append(float(v))
                except (ValueError, TypeError):
                    pass

            is_numeric = len(num_values) == len(values) and len(values) > 0

            col_stats: dict[str, Any] = {
                "total_rows": len(records),
                "non_null_count": len(values),
                "null_count": null_count,
                "unique_count": unique_count,
                "is_numeric": is_numeric,
            }

            if is_numeric and num_values:
                col_stats["min"] = min(num_values)
                col_stats["max"] = max(num_values)
                col_stats["sum"] = round(sum(num_values), 4)
                col_stats["mean"] = round(sum(num_values) / len(num_values), 4)

            summary[col] = col_stats

        return {
            "status": "ok",
            "records_count": len(records),
            "columns": summary,
        }
    except Exception as e:
        return {"status": "error", "error": f"Data summarization failed: {e!s}"}


def data_validate_schema(data: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Validate a dictionary against expected field types and presence."""
    type_map = {
        "str": str,
        "string": str,
        "int": int,
        "integer": int,
        "float": float,
        "number": (int, float),
        "bool": bool,
        "boolean": bool,
        "list": list,
        "array": list,
        "dict": dict,
        "object": dict,
    }

    missing_fields: list[str] = []
    type_mismatches: list[dict[str, Any]] = []

    for field, expected_type_str in schema.items():
        if field not in data:
            missing_fields.append(field)
            continue

        val = data[field]
        expected_type = type_map.get(str(expected_type_str).lower())
        if expected_type and not isinstance(val, expected_type):
            type_mismatches.append({
                "field": field,
                "expected": str(expected_type_str),
                "actual": type(val).__name__,
                "value": str(val)[:50],
            })

    is_valid = len(missing_fields) == 0 and len(type_mismatches) == 0
    return {
        "status": "ok",
        "valid": is_valid,
        "missing_fields": missing_fields,
        "type_mismatches": type_mismatches,
    }
