"""Tests for RepoFetcher."""

import zipfile
from pathlib import Path

import pytest

from harness.ingestion.fetcher import FetchError, RepoFetcher


@pytest.mark.unit
@pytest.mark.asyncio
class TestRepoFetcher:
    async def test_fetch_local_zip(self, tmp_path: Path) -> None:
        # Create a mock zip archive
        source_dir = tmp_path / "mock_repo"
        source_dir.mkdir()
        (source_dir / "plugin.json").write_text('{"name": "zipped-test", "version": "1.0.0"}')
        (source_dir / "main.py").write_text("def run(): pass")

        zip_path = tmp_path / "mock_repo.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(source_dir / "plugin.json", "mock_repo/plugin.json")
            zf.write(source_dir / "main.py", "mock_repo/main.py")

        plugin_cache_dir = tmp_path / "cache"
        fetcher = RepoFetcher(plugin_dir=plugin_cache_dir)

        extracted_dir = await fetcher.fetch(str(zip_path))
        assert extracted_dir.exists()
        assert (extracted_dir / "plugin.json").exists()

        # Cache listing
        cached = fetcher.list_cached()
        assert len(cached) == 1
        assert cached[0]["has_manifest"] is True

        # Remove cached
        assert fetcher.remove_cached(extracted_dir.name) is True
        assert not extracted_dir.exists()

    async def test_invalid_source(self, tmp_path: Path) -> None:
        fetcher = RepoFetcher(plugin_dir=tmp_path)
        with pytest.raises(FetchError):
            await fetcher.fetch("not a valid url or repo")
