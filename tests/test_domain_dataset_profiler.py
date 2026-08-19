"""Tests for Domain 3: Dataset Profiler plugin."""

from __future__ import annotations

import pytest

from plugins.data_engineering.dataset_profiler.main import (
    compute_correlation_matrix,
    detect_outliers_zscore,
    profile_tabular_dataset,
)


@pytest.mark.unit
class TestDatasetProfilerPlugin:
    def test_profile_tabular_dataset(self) -> None:
        records = [
            {"age": 25, "score": 88.5, "country": "US"},
            {"age": 30, "score": 92.0, "country": "CA"},
            {"age": 35, "score": None, "country": "US"},
        ]
        res = profile_tabular_dataset(records)
        assert res["status"] == "ok"
        assert res["row_count"] == 3
        assert res["columns"]["age"]["is_numeric"] is True
        assert res["columns"]["score"]["nulls"] == 1
        assert res["columns"]["country"]["uniques"] == 2

    def test_detect_outliers_zscore(self) -> None:
        values = [10.0, 11.0, 10.5, 9.8, 10.2, 100.0]  # 100.0 is an extreme outlier
        res = detect_outliers_zscore(values, threshold=2.0)
        assert res["status"] == "ok"
        assert res["outliers_count"] >= 1
        assert res["outliers"][0]["value"] == 100.0

    def test_compute_correlation_matrix(self) -> None:
        records = [
            {"x": 1.0, "y": 2.0},
            {"x": 2.0, "y": 4.0},
            {"x": 3.0, "y": 6.0},
        ]
        res = compute_correlation_matrix(records)
        assert res["status"] == "ok"
        assert res["matrix"]["x"]["y"] == 1.0  # Perfect positive correlation
