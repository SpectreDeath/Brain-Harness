"""Contract test suite for HfDatasets service decomposition per AGENTS.md Rules 11, 12, 40, 43, 49, 58."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext
from harness.services.hf_datasets import (
    HF_DATASETS_SERVICE_KEY,
    DefaultHfDatasetsService,
    HfColumnSchema,
    HfDatasetMetadata,
    HfDatasetVaultCommit,
    HfDatasetsService,
    HfStorageStrategy,
    HfStreamConfig,
    HfTransformationSpec,
    HfTransformResult,
    resolve_hf_datasets_service,
)
from harness.services.hf_datasets.lakehouse import convert_format, write_records
from harness.services.hf_datasets.profiler import evaluate_storage_strategy, profile_schema
from harness.services.hf_datasets.streamer import iter_records, probe_file_streaming
from harness.services.hf_datasets.transforms import transform_dataset
from harness.services.hf_datasets.vault import commit_to_vault


@pytest.mark.unit
class TestHfDatasetsDecompositionContracts:
    def test_submodule_line_count_invariants(self) -> None:
        """Rule 11: All decomposed submodules in harness/services/hf_datasets must be <= 200 lines."""
        pkg_dir = Path("src/harness/services/hf_datasets")
        assert pkg_dir.exists() and pkg_dir.is_dir()

        submodules = list(pkg_dir.glob("*.py"))
        assert len(submodules) >= 9, f"Expected at least 9 submodules, found {len(submodules)}"

        for mod in submodules:
            lines = len(mod.read_text(encoding="utf-8").splitlines())
            assert (
                lines <= 200
            ), f"Module {mod.name} exceeds 200 lines ({lines} lines). Violates Rule 11."

    def test_facade_and_package_reexports(self) -> None:
        """Verify 100% backward compatibility of re-exported symbols from harness.services and hf_datasets."""
        import harness.services as s
        import harness.services.hf_datasets as hfd

        for symbol in [
            "HF_DATASETS_SERVICE_KEY",
            "DefaultHfDatasetsService",
            "HfColumnSchema",
            "HfDatasetMetadata",
            "HfDatasetVaultCommit",
            "HfDatasetsService",
            "HfStorageStrategy",
            "HfStreamConfig",
            "HfTransformationSpec",
            "HfTransformResult",
        ]:
            assert hasattr(s, symbol)
            assert hasattr(hfd, symbol)
            assert getattr(s, symbol) is getattr(hfd, symbol)

    def test_single_seam_resolver(self) -> None:
        """Rule 58: resolve_hf_datasets_service must resolve existing binding or register default."""
        ctx = ServiceContext()
        custom_svc = DefaultHfDatasetsService()
        ctx.provide(HF_DATASETS_SERVICE_KEY, custom_svc)

        resolved = resolve_hf_datasets_service(ctx)
        assert resolved is custom_svc

        # Fallback resolution creates fresh instance and registers it
        empty_ctx = ServiceContext()
        auto_svc = resolve_hf_datasets_service(empty_ctx)
        assert isinstance(auto_svc, HfDatasetsService)
        assert empty_ctx.require(HF_DATASETS_SERVICE_KEY) is auto_svc

        # None context creates standalone instance
        standalone = resolve_hf_datasets_service(None)
        assert isinstance(standalone, HfDatasetsService)

    def test_slotted_frozen_dataclass_immutability(self) -> None:
        """Rule 12 & Rule 43: Slotted and frozen models reject attribute mutation."""
        meta = HfDatasetMetadata(name="test", split="train", num_rows=100)
        with pytest.raises((AttributeError, TypeError)):
            meta.name = "mutated"  # type: ignore[misc]

        col = HfColumnSchema(name="col", arrow_type="int64")
        with pytest.raises((AttributeError, TypeError)):
            col.arrow_type = "string"  # type: ignore[misc]

        res = HfTransformResult(
            status="ok",
            rows_processed=10,
            execution_time_ms=1.5,
            cache_fingerprint="abc",
        )
        with pytest.raises((AttributeError, TypeError)):
            res.rows_processed = 20  # type: ignore[misc]

    def test_streamer_direct_seam(self, tmp_path: Path) -> None:
        """Verify direct invocations of streamer submodule functions."""
        f = tmp_path / "stream_test.jsonl"
        f.write_text(
            json.dumps({"a": 1, "b": "x"}) + "\n" + json.dumps({"a": 2, "b": "y"}) + "\n",
            encoding="utf-8",
        )
        feats, count = probe_file_streaming(f)
        assert count == 2
        assert feats.get("a") == "int"

        records = list(iter_records(str(f), max_records=1))
        assert len(records) == 1
        assert records[0]["a"] == 1

    def test_transforms_direct_seam(self, tmp_path: Path) -> None:
        """Verify direct invocations of transforms submodule functions."""
        in_f = tmp_path / "in.jsonl"
        out_f = tmp_path / "out.jsonl"
        in_f.write_text(
            json.dumps({"x": 10, "y": "keep"}) + "\n" + json.dumps({"x": 5, "y": "drop"}) + "\n",
            encoding="utf-8",
        )
        spec = HfTransformationSpec(filter_field="x", filter_op="gt", filter_value=8)
        res = transform_dataset(str(in_f), str(out_f), spec)
        assert res.status == "ok"
        assert res.rows_processed == 1
        assert out_f.exists()

    def test_lakehouse_direct_seam(self, tmp_path: Path) -> None:
        """Verify direct invocations of lakehouse formatting and conversion."""
        in_f = tmp_path / "source.jsonl"
        out_csv = tmp_path / "target.csv"
        in_f.write_text(json.dumps({"id": 1, "val": "lake"}) + "\n", encoding="utf-8")

        res = convert_format(str(in_f), str(out_csv), target_format="csv")
        assert res.status == "ok"
        assert res.rows_processed == 1
        assert out_csv.exists()

    def test_profiler_direct_seam(self, tmp_path: Path) -> None:
        """Verify direct invocations of schema profiler and storage evaluator."""
        f = tmp_path / "profile.jsonl"
        f.write_text(json.dumps({"num": 42, "flag": True}) + "\n", encoding="utf-8")

        schemas = profile_schema(str(f))
        assert len(schemas) == 2
        types = {s.name: s.arrow_type for s in schemas}
        assert types["num"] == "int64"
        assert types["flag"] == "bool"

        strat = evaluate_storage_strategy(str(f), auto_stream_threshold_mb=100)
        assert strat.strategy == "mmap_arrow"

    def test_vault_commit_dual_file_directory(self, tmp_path: Path) -> None:
        """Rule 40: commit_to_vault must generate metadata.json and summary.md."""
        meta = HfDatasetMetadata(name="corpus", split="train", num_rows=50)
        schemas = [HfColumnSchema(name="id", arrow_type="int64")]
        vault_root = tmp_path / "vault"

        commit = commit_to_vault("corpus", meta, schemas, vault_root=str(vault_root))
        assert Path(commit.metadata_path).name == "metadata.json"
        assert Path(commit.summary_path).name == "summary.md"
        assert Path(commit.metadata_path).exists()
        assert Path(commit.summary_path).exists()
