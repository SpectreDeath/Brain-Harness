"""Comprehensive unit tests and immutability contracts for HfDatasets service and models."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from harness.commands.datasets import datasets_group
from harness.kernel.context import ServiceContext
from harness.services.hf_datasets import (
    HF_DATASETS_SERVICE_KEY,
    DefaultHfDatasetsService,
    HfColumnSchema,
    HfDatasetMetadata,
    HfDatasetsService,
    HfDatasetVaultCommit,
    HfStorageStrategy,
    HfStreamConfig,
    HfTransformationSpec,
    HfTransformResult,
)


@pytest.mark.unit
class TestHfDatasetsDomainModels:
    """Validate slotted/frozen dataclass invariants and __post_init__ assertions (Rule 12, Rule 43)."""

    def test_metadata_immutability_and_validation(self) -> None:
        meta = HfDatasetMetadata(
            name="imdb",
            split="train",
            num_rows=25000,
            features={"text": "string", "label": "int64"},
            format="parquet",
            byte_size=12000000,
            is_streaming=False,
        )
        assert meta.name == "imdb"
        assert meta.num_rows == 25000

        # Rule 43: direct assignment immutability check
        with pytest.raises((AttributeError, TypeError)):
            meta.name = "new_name"  # type: ignore[misc]

        with pytest.raises((AttributeError, TypeError)):
            meta.num_rows = 50  # type: ignore[misc]

        # Post-init validation checks
        with pytest.raises(ValueError, match="name cannot be empty"):
            HfDatasetMetadata(name="", split="train", num_rows=10)

        with pytest.raises(ValueError, match="num_rows must be non-negative"):
            HfDatasetMetadata(name="test", split="train", num_rows=-5)

    def test_stream_config_immutability_and_validation(self) -> None:
        config = HfStreamConfig(batch_size=50, buffer_size=500, max_samples=20)
        assert config.batch_size == 50

        with pytest.raises((AttributeError, TypeError)):
            config.batch_size = 100  # type: ignore[misc]

        with pytest.raises(ValueError, match="batch_size must be positive"):
            HfStreamConfig(batch_size=0)

        with pytest.raises(ValueError, match="max_samples must be positive"):
            HfStreamConfig(max_samples=-1)

    def test_column_schema_immutability_and_validation(self) -> None:
        col = HfColumnSchema(
            name="tokens",
            arrow_type="list",
            is_nullable=False,
            feature_type="Sequence",
            sample_values=([1, 2, 3],),
        )
        assert col.name == "tokens"

        with pytest.raises((AttributeError, TypeError)):
            col.arrow_type = "string"  # type: ignore[misc]

        with pytest.raises(ValueError, match="name cannot be empty"):
            HfColumnSchema(name="  ", arrow_type="int64")

    def test_transform_result_immutability(self) -> None:
        res = HfTransformResult(
            status="ok",
            rows_processed=100,
            execution_time_ms=12.5,
            cache_fingerprint="abc12345",
            output_path="/tmp/out.parquet",
        )
        assert res.rows_processed == 100

        with pytest.raises((AttributeError, TypeError)):
            res.status = "failed"  # type: ignore[misc]

        with pytest.raises(ValueError, match="status cannot be empty"):
            HfTransformResult(
                status="",
                rows_processed=0,
                execution_time_ms=0.0,
                cache_fingerprint="abc",
            )

    def test_storage_strategy_immutability_and_validation(self) -> None:
        strat = HfStorageStrategy(
            strategy="mmap_arrow",
            reason="Fits in memory",
            estimated_bytes=1024,
            recommended_batch_size=500,
            recommended_workers=1,
            requires_streaming=False,
        )
        assert strat.strategy == "mmap_arrow"

        with pytest.raises((AttributeError, TypeError)):
            strat.strategy = "lazy_stream"  # type: ignore[misc]

        with pytest.raises(ValueError, match="strategy cannot be empty"):
            HfStorageStrategy(
                strategy="",
                reason="none",
                estimated_bytes=0,
                recommended_batch_size=100,
                recommended_workers=1,
                requires_streaming=False,
            )

    def test_transformation_spec_immutability(self) -> None:
        spec = HfTransformationSpec(
            filter_field="score",
            filter_op="gt",
            filter_value=50,
            select_columns=("id", "score"),
            batch_size=200,
        )
        assert spec.filter_field == "score"

        with pytest.raises((AttributeError, TypeError)):
            spec.batch_size = 50  # type: ignore[misc]

        with pytest.raises(ValueError, match="batch_size must be positive"):
            HfTransformationSpec(batch_size=0)

    def test_vault_commit_immutability(self) -> None:
        commit = HfDatasetVaultCommit(
            ki_id="ki_dataset_test_123",
            title="Dataset Catalog: test",
            summary="Catalogued test",
            metadata_path="/vault/meta.json",
            summary_path="/vault/summary.md",
            cache_fingerprint="12345678",
            features_count=5,
            total_rows=1000,
        )
        assert commit.ki_id == "ki_dataset_test_123"

        with pytest.raises((AttributeError, TypeError)):
            commit.total_rows = 2000  # type: ignore[misc]

        with pytest.raises(ValueError, match="ki_id cannot be empty"):
            HfDatasetVaultCommit(
                ki_id="",
                title="title",
                summary="summary",
                metadata_path="m",
                summary_path="s",
                cache_fingerprint="c",
                features_count=1,
                total_rows=1,
            )


@pytest.mark.unit
class TestDefaultHfDatasetsService:
    """Validate 5-stage pipeline behavior in DefaultHfDatasetsService."""

    @pytest.fixture
    def engine(self) -> DefaultHfDatasetsService:
        return DefaultHfDatasetsService()

    @pytest.fixture
    def sample_jsonl(self, tmp_path: Path) -> Path:
        p = tmp_path / "dataset.jsonl"
        lines = [
            json.dumps({"id": 1, "text": "harness first", "score": 95, "active": True}),
            json.dumps(
                {"id": 2, "text": "harness second", "score": 82, "active": False}
            ),
            json.dumps({"id": 3, "text": "other record", "score": 45, "active": True}),
            json.dumps({"id": 4, "text": "harness third", "score": 78, "active": True}),
        ]
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return p

    def test_protocol_conformance(self, engine: DefaultHfDatasetsService) -> None:
        assert isinstance(engine, HfDatasetsService)

    def test_stage_1_inspect_dataset(
        self, engine: DefaultHfDatasetsService, sample_jsonl: Path
    ) -> None:
        meta = engine.inspect_dataset(str(sample_jsonl))
        assert meta.name == "dataset"
        assert meta.split == "train"
        assert meta.num_rows == 4
        assert meta.format == "jsonl"
        assert meta.byte_size > 0
        assert not meta.is_streaming

        # Remote / simulated hub dataset
        remote_meta = engine.inspect_dataset("rotten_tomatoes", split="test")
        assert remote_meta.name == "rotten_tomatoes"
        assert remote_meta.split == "test"
        assert remote_meta.is_streaming

    def test_stage_2_storage_strategy_evaluation(
        self, engine: DefaultHfDatasetsService, sample_jsonl: Path
    ) -> None:
        # Small dataset should recommend mmap_arrow
        strat = engine.evaluate_storage_strategy(
            str(sample_jsonl), auto_stream_threshold_mb=10
        )
        assert strat.strategy == "mmap_arrow"
        assert not strat.requires_streaming
        assert strat.recommended_batch_size == 500

        # Dataset exceeding threshold should recommend lazy_stream
        strat_stream = engine.evaluate_storage_strategy(
            str(sample_jsonl),
            auto_stream_threshold_mb=0,  # force stream
        )
        assert strat_stream.strategy == "lazy_stream"
        assert strat_stream.requires_streaming
        assert strat_stream.recommended_batch_size == 100

    def test_stage_3_stream_sample_bounded(
        self, engine: DefaultHfDatasetsService, sample_jsonl: Path
    ) -> None:
        samples = engine.stream_sample(str(sample_jsonl), max_samples=2)
        assert len(samples) == 2
        assert samples[0]["id"] == 1
        assert samples[1]["id"] == 2

    def test_stage_1_profile_schema(
        self, engine: DefaultHfDatasetsService, sample_jsonl: Path
    ) -> None:
        schemas = engine.profile_schema(str(sample_jsonl))
        assert len(schemas) == 4
        by_name = {s.name: s for s in schemas}
        assert by_name["id"].arrow_type == "int64"
        assert by_name["text"].arrow_type == "string"
        assert by_name["score"].arrow_type == "int64"
        assert by_name["active"].arrow_type == "bool"

    def test_stage_3_transform_dataset(
        self, engine: DefaultHfDatasetsService, sample_jsonl: Path, tmp_path: Path
    ) -> None:
        out_p = tmp_path / "filtered.jsonl"
        spec = HfTransformationSpec(
            filter_field="score",
            filter_op="gt",
            filter_value=80,
            select_columns=("id", "score"),
            batch_size=50,
        )
        res = engine.transform_dataset(str(sample_jsonl), str(out_p), spec)
        assert res.status == "ok"
        assert res.rows_processed == 2
        assert out_p.exists()

        records = [
            json.loads(line)
            for line in out_p.read_text(encoding="utf-8").splitlines()
            if line
        ]
        assert len(records) == 2
        assert all(r["score"] > 80 for r in records)
        assert all(set(r.keys()) == {"id", "score"} for r in records)

    def test_stage_4_convert_format(
        self, engine: DefaultHfDatasetsService, sample_jsonl: Path, tmp_path: Path
    ) -> None:
        csv_out = tmp_path / "converted.csv"
        res_csv = engine.convert_format(
            str(sample_jsonl), str(csv_out), target_format="csv"
        )
        assert res_csv.status == "ok"
        assert res_csv.rows_processed == 4
        assert csv_out.exists()

        # Lakehouse columnar format
        parquet_out = tmp_path / "converted.parquet"
        res_pq = engine.convert_format(
            str(sample_jsonl), str(parquet_out), target_format="parquet"
        )
        assert res_pq.status == "ok"
        assert res_pq.rows_processed == 4
        assert parquet_out.exists()

    def test_stage_5_commit_to_vault(
        self, engine: DefaultHfDatasetsService, sample_jsonl: Path, tmp_path: Path
    ) -> None:
        meta = engine.inspect_dataset(str(sample_jsonl))
        schemas = engine.profile_schema(str(sample_jsonl))
        vault_root = tmp_path / "knowledge_vault"

        commit = engine.commit_to_vault(
            "imdb_test", meta, schemas, vault_root=str(vault_root)
        )
        assert commit.ki_id.startswith("ki_dataset_imdb_test_")
        assert Path(commit.metadata_path).exists()
        assert Path(commit.summary_path).exists()
        assert commit.features_count == 4
        assert commit.total_rows == 4

        # Verify dual-file directory contents (Rule 40)
        meta_dict = json.loads(Path(commit.metadata_path).read_text(encoding="utf-8"))
        assert meta_dict["id"] == commit.ki_id
        assert meta_dict["dataset"]["num_rows"] == 4

        summary_md = Path(commit.summary_path).read_text(encoding="utf-8")
        assert "## Schema Definition" in summary_md
        assert "## Epistemic Checkpoint" in summary_md


@pytest.mark.unit
class TestHfDatasetsClickCli:
    """Validate Click CLI headless subcommands (Rule 10)."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        return CliRunner()

    @pytest.fixture
    def data_file(self, tmp_path: Path) -> Path:
        f = tmp_path / "cli_test.jsonl"
        f.write_text(
            json.dumps({"colA": 10, "colB": "test"})
            + "\n"
            + json.dumps({"colA": 20, "colB": "sample"})
            + "\n",
            encoding="utf-8",
        )
        return f

    def test_cli_inspect_and_profile(self, runner: CliRunner, data_file: Path) -> None:
        res = runner.invoke(datasets_group, ["inspect", str(data_file)])
        assert res.exit_code == 0
        parsed = json.loads(res.output)
        assert parsed["name"] == "cli_test"
        assert parsed["num_rows"] == 2

        res_prof = runner.invoke(datasets_group, ["profile", str(data_file)])
        assert res_prof.exit_code == 0
        prof_parsed = json.loads(res_prof.output)
        assert len(prof_parsed) == 2

    def test_cli_strategy_and_sample(self, runner: CliRunner, data_file: Path) -> None:
        res_strat = runner.invoke(
            datasets_group, ["strategy", str(data_file), "--threshold-mb", "100"]
        )
        assert res_strat.exit_code == 0
        strat_parsed = json.loads(res_strat.output)
        assert strat_parsed["strategy"] in ("mmap_arrow", "lazy_stream")

        res_sample = runner.invoke(
            datasets_group, ["sample", str(data_file), "--n", "1"]
        )
        assert res_sample.exit_code == 0
        samples = json.loads(res_sample.output)
        assert len(samples) == 1

    def test_cli_transform_and_convert(
        self, runner: CliRunner, data_file: Path, tmp_path: Path
    ) -> None:
        out_tf = tmp_path / "out_tf.jsonl"
        res_tf = runner.invoke(
            datasets_group,
            [
                "transform",
                str(data_file),
                str(out_tf),
                "--filter-field",
                "colA",
                "--filter-op",
                "eq",
                "--filter-val",
                "10",
            ],
        )
        assert res_tf.exit_code == 0
        assert out_tf.exists()

        out_conv = tmp_path / "out_conv.csv"
        res_conv = runner.invoke(
            datasets_group,
            ["convert", str(data_file), str(out_conv), "--format", "csv"],
        )
        assert res_conv.exit_code == 0
        assert out_conv.exists()

    def test_cli_commit_vault(
        self, runner: CliRunner, data_file: Path, tmp_path: Path
    ) -> None:
        vault_dir = tmp_path / "vault"
        res = runner.invoke(
            datasets_group,
            [
                "commit-vault",
                "cli_dataset",
                str(data_file),
                "--vault-root",
                str(vault_dir),
            ],
        )
        assert res.exit_code == 0
        parsed = json.loads(res.output)
        assert parsed["status"] == "ok"
        assert parsed["ki_id"].startswith("ki_dataset_cli_dataset_")


@pytest.mark.unit
class TestHfDatasetsIoCIntegration:
    """Validate IoC service registration and resolution (Rule 2)."""

    def test_ioc_provide_and_require(self) -> None:
        ctx = ServiceContext()
        service = DefaultHfDatasetsService()
        ctx.provide(HF_DATASETS_SERVICE_KEY, service, provider="test")

        resolved = ctx.require(HF_DATASETS_SERVICE_KEY)
        assert resolved is service
        assert isinstance(resolved, HfDatasetsService)
