"""Unit tests for the domain.hf_datasets plugin."""

import json
from pathlib import Path

import pytest

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.hf_datasets import (
    HF_DATASETS_SERVICE_KEY,
)
from plugins.data_engineering.hf_datasets.main import (
    HfDatasetsPlugin,
    hf_commit_to_vault,
    hf_convert_format,
    hf_evaluate_storage_strategy,
    hf_inspect_dataset,
    hf_profile_schema,
    hf_stream_sample,
    hf_transform_dataset,
    plugin,
)


@pytest.mark.unit
class TestHfDatasetsPlugin:
    """Test suite for HfDatasetsPlugin lifecycle and service delegation."""

    @pytest.mark.asyncio
    async def test_plugin_validation(self) -> None:
        plugin_dir = Path(__file__).parent
        report = await PluginValidator.validate(plugin_dir)
        assert report.valid, (
            f"Plugin validation failed: {[c.message for c in report.checks if not c.passed]}"
        )

    def test_plugin_metadata(self) -> None:
        assert plugin.name == "domain.hf_datasets"
        assert plugin.version == "1.0.0"
        assert HF_DATASETS_SERVICE_KEY in plugin.provides
        assert plugin.requires == []

    @pytest.mark.asyncio
    async def test_plugin_lifecycle(self) -> None:
        ctx = ServiceContext()
        test_plugin = HfDatasetsPlugin()

        await test_plugin.on_load(ctx)
        resolved = ctx.require(HF_DATASETS_SERVICE_KEY)
        assert resolved is test_plugin

        await test_plugin.on_enable()
        await test_plugin.on_disable()
        await test_plugin.on_unload()

    def test_inspect_and_sample_tools(self, tmp_path: Path) -> None:
        sample_file = tmp_path / "test_data.jsonl"
        sample_file.write_text(
            json.dumps({"id": 1, "text": "hello", "score": 0.95})
            + "\n"
            + json.dumps({"id": 2, "text": "world", "score": 0.88})
            + "\n",
            encoding="utf-8",
        )

        inspect_res = hf_inspect_dataset(str(sample_file))
        assert inspect_res["status"] == "ok"
        assert inspect_res["name"] == "test_data"
        assert inspect_res["num_rows"] == 2

        sample_res = hf_stream_sample(str(sample_file), max_samples=1)
        assert sample_res["status"] == "ok"
        assert sample_res["sample_count"] == 1
        assert sample_res["records"][0]["id"] == 1

    def test_storage_strategy_tool(self, tmp_path: Path) -> None:
        sample_file = tmp_path / "strat_data.jsonl"
        sample_file.write_text(json.dumps({"x": 1}) + "\n", encoding="utf-8")

        res = hf_evaluate_storage_strategy(str(sample_file))
        assert res["status"] == "ok"
        assert res["strategy"] in ("mmap_arrow", "lazy_stream")
        assert res["recommended_batch_size"] > 0

    def test_profile_schema_tool(self, tmp_path: Path) -> None:
        sample_file = tmp_path / "profile_data.json"
        sample_file.write_text(
            json.dumps(
                [
                    {"user_id": 101, "active": True, "balance": 450.50},
                    {"user_id": 102, "active": False, "balance": 120.00},
                ]
            ),
            encoding="utf-8",
        )

        profile_res = hf_profile_schema(str(sample_file))
        assert profile_res["status"] == "ok"
        cols = {c["name"]: c for c in profile_res["columns"]}
        assert "user_id" in cols
        assert cols["user_id"]["arrow_type"] == "int64"
        assert cols["active"]["arrow_type"] == "bool"
        assert cols["balance"]["arrow_type"] == "double"

    def test_transform_dataset_tool(self, tmp_path: Path) -> None:
        src_file = tmp_path / "src.jsonl"
        src_file.write_text(
            json.dumps({"id": 1, "val": 10})
            + "\n"
            + json.dumps({"id": 2, "val": 50})
            + "\n",
            encoding="utf-8",
        )
        dst_file = tmp_path / "transformed.jsonl"

        res = hf_transform_dataset(
            str(src_file),
            str(dst_file),
            filter_field="val",
            filter_op="gt",
            filter_value=20,
            select_columns=["id", "val"],
        )
        assert res["status"] == "ok"
        assert res["rows_processed"] == 1
        assert dst_file.exists()

    def test_convert_format_tool(self, tmp_path: Path) -> None:
        src_file = tmp_path / "source.json"
        src_file.write_text(
            json.dumps([{"x": 10, "y": 20}, {"x": 30, "y": 40}]), encoding="utf-8"
        )
        dst_file = tmp_path / "converted.csv"

        conv_res = hf_convert_format(str(src_file), str(dst_file), target_format="csv")
        assert conv_res["status"] == "ok"
        assert conv_res["rows_processed"] == 2
        assert dst_file.exists()

    def test_commit_to_vault_tool(self, tmp_path: Path) -> None:
        src_file = tmp_path / "vault_source.jsonl"
        src_file.write_text(
            json.dumps({"col1": "val1", "col2": 100}) + "\n", encoding="utf-8"
        )
        vault_root = tmp_path / "vault"

        res = hf_commit_to_vault(
            "plugin_dataset", str(src_file), vault_root=str(vault_root)
        )
        assert res["status"] == "ok"
        assert Path(res["metadata_path"]).exists()
        assert Path(res["summary_path"]).exists()
