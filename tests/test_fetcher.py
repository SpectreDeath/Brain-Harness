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

    async def test_fetch_local_zip_rejects_traversal_member(self, tmp_path: Path) -> None:
        zip_path = tmp_path / "evil.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("../evil.txt", "escaped")
            zf.writestr("good.txt", "ok")

        fetcher = RepoFetcher(plugin_dir=tmp_path / "cache")
        with pytest.raises(FetchError):
            await fetcher.fetch(str(zip_path))

        # Nothing escaped the target directory, and nothing was planted in it.
        assert not (tmp_path / "evil.txt").exists()
        assert not (tmp_path / "cache" / "evil" / "evil.txt").exists()

    async def test_fetch_local_zip_rejects_absolute_member(self, tmp_path: Path) -> None:
        zip_path = tmp_path / "evil.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("/tmp/evil.txt", "escaped")

        fetcher = RepoFetcher(plugin_dir=tmp_path / "cache")
        with pytest.raises(FetchError):
            await fetcher.fetch(str(zip_path))

        assert not (tmp_path / "cache" / "evil" / "tmp" / "evil.txt").exists()

    async def test_fetch_local_zip_rejects_exceeded_file_count(self, tmp_path: Path) -> None:
        zip_path = tmp_path / "many_files.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for i in range(15):
                zf.writestr(f"file_{i}.txt", f"data {i}")

        fetcher = RepoFetcher(plugin_dir=tmp_path / "cache", max_extract_files=10)
        with pytest.raises(FetchError, match="too many members"):
            await fetcher.fetch(str(zip_path))

    async def test_fetch_local_zip_rejects_exceeded_total_bytes(self, tmp_path: Path) -> None:
        zip_path = tmp_path / "large_files.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("big.bin", b"0" * 5000)

        fetcher = RepoFetcher(plugin_dir=tmp_path / "cache", max_extract_bytes=1000)
        with pytest.raises(FetchError, match="exceeds total uncompressed size limit"):
            await fetcher.fetch(str(zip_path))

    async def test_fetch_local_zip_rejects_compression_bomb(self, tmp_path: Path) -> None:
        zip_path = tmp_path / "bomb.zip"
        # 2 MB of zeroes compresses to very few bytes (> 100:1 ratio)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("huge_zeroes.bin", b"\x00" * (2 * 1024 * 1024))

        fetcher = RepoFetcher(plugin_dir=tmp_path / "cache", max_extract_bytes=10 * 1024 * 1024)
        with pytest.raises(FetchError, match="suspicious compression ratio"):
            await fetcher.fetch(str(zip_path))

    async def test_streaming_download_bounds_enforced(self, tmp_path: Path) -> None:
        fetcher = RepoFetcher(plugin_dir=tmp_path / "cache", max_download_bytes=100)
        from unittest.mock import AsyncMock, patch

        mock_resp = AsyncMock()
        mock_resp.content = b"x" * 200
        mock_resp.raise_for_status = lambda: None

        with patch("httpx.AsyncClient.get", return_value=mock_resp):
            with pytest.raises(FetchError, match="Download size exceeded"):
                await fetcher.fetch("https://example.com/downloads/big_tool.zip")

    async def test_remote_zip_cache_key_collision_prevention(self, tmp_path: Path) -> None:
        """Verify two remote URLs with identical filename stems do not collide."""
        from unittest.mock import AsyncMock, patch
        import json

        def make_zip_bytes(name: str) -> bytes:
            buf_path = tmp_path / f"{name}.zip"
            with zipfile.ZipFile(buf_path, "w") as zf:
                zf.writestr("plugin.json", json.dumps({"name": name, "version": "1.0.0"}))
            return buf_path.read_bytes()

        fetcher = RepoFetcher(plugin_dir=tmp_path / "cache")

        mock_resp1 = AsyncMock()
        mock_resp1.content = make_zip_bytes("service_a")
        mock_resp1.raise_for_status = lambda: None

        mock_resp2 = AsyncMock()
        mock_resp2.content = make_zip_bytes("service_b")
        mock_resp2.raise_for_status = lambda: None

        url1 = "https://server-one.internal/plugins/tools.zip"
        url2 = "https://server-two.internal/plugins/tools.zip"

        with patch("httpx.AsyncClient.get", side_effect=[mock_resp1, mock_resp2]):
            dir1 = await fetcher.fetch(url1)
            dir2 = await fetcher.fetch(url2)

        # Both directories exist and are distinct
        assert dir1 != dir2
        assert dir1.exists()
        assert dir2.exists()

        # Both have their respective content without collision
        manifest1 = json.loads((dir1 / "plugin.json").read_text(encoding="utf-8"))
        manifest2 = json.loads((dir2 / "plugin.json").read_text(encoding="utf-8"))
        assert manifest1["name"] == "service_a"
        assert manifest2["name"] == "service_b"

        # Validate .cache_meta.json exists in both
        meta1 = json.loads((dir1 / ".cache_meta.json").read_text(encoding="utf-8"))
        meta2 = json.loads((dir2 / ".cache_meta.json").read_text(encoding="utf-8"))
        assert meta1["source"] == url1
        assert meta2["source"] == url2

    async def test_local_zip_cache_invalidation_on_change(self, tmp_path: Path) -> None:
        """Verify modifying local zip causes re-extraction and updates cache metadata."""
        import json
        import time

        zip_dir = tmp_path / "sources"
        zip_dir.mkdir()
        zip_path = zip_dir / "tool.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("plugin.json", json.dumps({"name": "v1", "version": "1.0.0"}))

        fetcher = RepoFetcher(plugin_dir=tmp_path / "cache")
        dir_v1 = await fetcher.fetch(str(zip_path))
        m1 = json.loads((dir_v1 / "plugin.json").read_text(encoding="utf-8"))
        assert m1["name"] == "v1"

        # Modify the zip (different size and mtime)
        time.sleep(0.01)
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("plugin.json", json.dumps({"name": "v2_updated", "version": "2.0.0"}))

        dir_v2 = await fetcher.fetch(str(zip_path))
        m2 = json.loads((dir_v2 / "plugin.json").read_text(encoding="utf-8"))
        assert m2["name"] == "v2_updated"
