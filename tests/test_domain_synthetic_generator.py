"""Tests for Domain 3: Synthetic Generator plugin."""

from __future__ import annotations

import pytest

from plugins.data_engineering.synthetic_generator.main import (
    generate_mock_records,
    generate_synthetic_timeseries,
)


@pytest.mark.unit
class TestSyntheticGeneratorPlugin:
    def test_generate_mock_records(self) -> None:
        schema = {
            "user_id": "uuid",
            "full_name": "name",
            "email_addr": "email",
            "age": "int:20:50",
            "plan": "enum:free,pro,enterprise",
        }
        res = generate_mock_records(schema, count=5, seed=42)
        assert res["status"] == "ok"
        assert res["record_count"] == 5
        assert len(res["records"]) == 5
        for r in res["records"]:
            assert 20 <= r["age"] <= 50
            assert r["plan"] in ("free", "pro", "enterprise")
            assert "@" in r["email_addr"]

    def test_generate_synthetic_timeseries(self) -> None:
        res = generate_synthetic_timeseries(days=14, baseline=200.0, trend=1.0)
        assert res["status"] == "ok"
        assert res["days"] == 14
        assert len(res["series"]) == 14
        assert res["series"][0]["value"] > 100.0
