"""Contract tests for hf-datasets-engineer skill domain models and engine."""

import json
import pytest
from pathlib import Path

from harness.services.hf_datasets import (
    HfColumnSchema,
    HfDatasetMetadata,
    HfStreamConfig,
    HfTransformResult,
)
from plugins.data_engineering.hf_datasets.service import HfDatasetsServiceImpl


@pytest.mark.unit
class TestHfDatasetsEngineerSkill:
    """Test suite verifying slotted domain models, immutability, and execution logic."""

    def test_slotted_frozen_immutability(self) -> None:
        meta = HfDatasetMetadata(
            name="test_ds",
            split="train",
            num_rows=500,
            features={"text": "string"},
            format="arrow",
            byte_size=1024,
            is_streaming=False,
        )
        assert meta.name == "test_ds"
        assert meta.num_rows == 500

        # Frozen dataclass mutation invariant (Rule 43)
        with pytest.raises((AttributeError, TypeError)):
            meta.name = "mutated"  # type: ignore

    def test_construction_invariants(self) -> None:
        # Empty name should raise ValueError
        with pytest.raises(ValueError):
            HfDatasetMetadata(name="", split="train", num_rows=10)

        # Negative rows should raise ValueError
        with pytest.raises(ValueError):
            HfDatasetMetadata(name="valid", split="train", num_rows=-5)

        # Non-positive batch_size should raise ValueError
        with pytest.raises(ValueError):
            HfStreamConfig(batch_size=0)

    def test_schema_profiling_and_conversion(self, tmp_path: Path) -> None:
        engine = HfDatasetsServiceImpl()
        src = tmp_path / "data.jsonl"
        src.write_text(
            json.dumps({"city": "Tokyo", "population": 14000000, "is_capital": True}) + "\n" +
            json.dumps({"city": "Kyoto", "population": 1460000, "is_capital": False}) + "\n",
            encoding="utf-8"
        )

        # Test profile
        schemas = engine.profile_schema(str(src))
        col_map = {s.name: s for s in schemas}
        assert "city" in col_map
        assert col_map["city"].arrow_type == "string"
        assert col_map["population"].arrow_type == "int64"
        assert col_map["is_capital"].arrow_type == "bool"

        # Test convert
        dst = tmp_path / "data.csv"
        res = engine.convert_format(str(src), str(dst), target_format="csv")
        assert res.status == "ok"
        assert res.rows_processed == 2
        assert len(res.cache_fingerprint) == 16
        assert dst.exists()
