"""Tests for data_transformer plugin."""

from __future__ import annotations

import pytest

from plugins.data_transformer.main import (
    data_convert_format,
    data_filter_table,
    data_summarize_stats,
    data_validate_schema,
)


@pytest.mark.unit
class TestDataTransformerPlugin:
    def test_json_csv_toml_conversions(self) -> None:
        json_str = '[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]'

        # JSON -> CSV
        res_csv = data_convert_format(json_str, "json", "csv")
        assert res_csv["status"] == "ok"
        assert "name,age" in res_csv["converted_content"]
        assert "Alice,30" in res_csv["converted_content"]

        # CSV -> JSON
        res_json = data_convert_format(res_csv["converted_content"], "csv", "json")
        assert res_json["status"] == "ok"
        assert '"name": "Alice"' in res_json["converted_content"]

        # JSON -> TOML (dict wrapper)
        toml_in = '{"title": "Config", "version": 1}'
        res_toml = data_convert_format(toml_in, "json", "toml")
        assert res_toml["status"] == "ok"
        assert 'title = "Config"' in res_toml["converted_content"]

    def test_data_filter_table(self) -> None:
        records = [
            {"id": 1, "role": "admin", "score": 95},
            {"id": 2, "role": "user", "score": 80},
            {"id": 3, "role": "user", "score": 90},
        ]

        # Filter by role == user, sort by score descending
        res = data_filter_table(records, filters={"role": "user"}, sort_by="score", descending=True)
        assert res["status"] == "ok"
        assert res["matched_records_count"] == 2
        assert res["records"][0]["id"] == 3
        assert res["records"][1]["id"] == 2

    def test_data_summarize_stats(self) -> None:
        records = [
            {"name": "A", "val": 10},
            {"name": "B", "val": 20},
            {"name": "C", "val": 30},
        ]
        res = data_summarize_stats(records)
        assert res["status"] == "ok"
        stats = res["columns"]["val"]
        assert stats["is_numeric"] is True
        assert stats["min"] == 10.0
        assert stats["max"] == 30.0
        assert stats["mean"] == 20.0
        assert stats["sum"] == 60.0

    def test_data_validate_schema(self) -> None:
        schema = {
            "name": "string",
            "age": "integer",
            "active": "boolean",
        }

        # Valid payload
        valid_data = {"name": "Alice", "age": 30, "active": True}
        res_valid = data_validate_schema(valid_data, schema)
        assert res_valid["valid"] is True
        assert len(res_valid["missing_fields"]) == 0

        # Invalid payload with missing field and wrong type
        invalid_data = {"name": "Alice", "age": "thirty"}
        res_invalid = data_validate_schema(invalid_data, schema)
        assert res_invalid["valid"] is False
        assert "active" in res_invalid["missing_fields"]
        assert len(res_invalid["type_mismatches"]) == 1
        assert res_invalid["type_mismatches"][0]["field"] == "age"
