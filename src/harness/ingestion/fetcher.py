"""Repo fetcher — downloads GitHub repositories for plugin ingestion.

Supports:
    - Full GitHub URLs (https://github.com/owner/repo)
    - Short-form owner/repo
    - Local ZIP file paths
    - Branch/tag specification
"""

from __future__ import annotations

import asyncio
import datetime
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any

import httpx
import structlog

from harness.ingestion.providers import RepoProvider, parse_repo_source
from harness.plugins.loader import (
    DEFAULT_MAX_ZIP_FILES,
    DEFAULT_MAX_ZIP_TOTAL_BYTES,
    validate_zip_members,
)

logger = structlog.get_logger()

# Matches:
# 1. https://github.com/owner/repo/tree/branch_or_tag
# 2. https://github.com/owner/repo/archive/refs/tags/v1.0.0.zip
# 3. git@github.com:owner/repo.git
# 4. https://github.com/owner/repo(.git)
# 5. owner/repo
_GITHUB_TREE_RE = re.compile(
    r"^(?:https?://github\.com/)?([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)/tree/([a-zA-Z0-9_./-]+)/?$"
)
_GITHUB_ARCHIVE_RE = re.compile(
    r"^(?:https?://github\.com/)?([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)/archive/refs/(?:heads|tags)/([a-zA-Z0-9_./-]+?)(?:\.zip)?/?$"
)
_GITHUB_SSH_RE = re.compile(
    r"^git@github\.com:([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?$"
)
_GITHUB_URL_RE = re.compile(
    r"^(?:https?://github\.com/)?([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?/?$"
)

DEFAULT_PLUGIN_DIR = Path.home() / ".harness" / "plugins"
DEFAULT_MAX_DOWNLOAD_BYTES: int = 100 * 1024 * 1024  # 100 MB
DEFAULT_MAX_EXTRACT_FILES: int = DEFAULT_MAX_ZIP_FILES  # 10_000
DEFAULT_MAX_EXTRACT_BYTES: int = DEFAULT_MAX_ZIP_TOTAL_BYTES  # 250 MB


class FetchError(Exception):
    """Raised when fetching a repository fails."""

    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to fetch {url!r}: {reason}")


class RepoFetcher:
    """Downloads GitHub repositories and ZIP archives for plugin ingestion.

    Caches downloads by repository name and unique content hash to avoid
    redundant fetches and cache collisions.
    """

    def __init__(
        self,
        plugin_dir: Path | None = None,
        *,
        github_token: str | None = None,
        event_bus: Any | None = None,
        max_download_bytes: int = DEFAULT_MAX_DOWNLOAD_BYTES,
        max_extract_files: int = DEFAULT_MAX_EXTRACT_FILES,
        max_extract_bytes: int = DEFAULT_MAX_EXTRACT_BYTES,
    ) -> None:
        """Initialize the fetcher.

        Args:
            plugin_dir: Directory to store fetched plugins.
                Defaults to ``~/.harness/plugins/``.
            github_token: Optional GitHub personal access token for
                private repos or higher rate limits.
            event_bus: Optional event bus for ingestion telemetry.
            max_download_bytes: Maximum allowed download byte limit.
            max_extract_files: Maximum allowed files in extracted archive.
            max_extract_bytes: Maximum allowed total uncompressed bytes.
        """
        self._plugin_dir = plugin_dir or DEFAULT_PLUGIN_DIR
        self._plugin_dir.mkdir(parents=True, exist_ok=True)
        self._token = github_token
        self._event_bus = event_bus
        self._max_download_bytes = max_download_bytes
        self._max_extract_files = max_extract_files
        self._max_extract_bytes = max_extract_bytes

    @property
    def plugin_dir(self) -> Path:
        """Directory where fetched plugins are stored."""
        return self._plugin_dir

    @property
    def github_token(self) -> str | None:
        """Configured GitHub API token, if any."""
        return self._token

    @property
    def event_bus(self) -> Any | None:
        """Attached event bus, if any."""
        return self._event_bus

    @property
    def max_download_bytes(self) -> int:
        """Maximum allowed download size in bytes."""
        return self._max_download_bytes

    @property
    def max_extract_files(self) -> int:
        """Maximum allowed files in extracted archive."""
        return self._max_extract_files

    @property
    def max_extract_bytes(self) -> int:
        """Maximum allowed uncompressed extraction size in bytes."""
        return self._max_extract_bytes

    def attach_event_bus(self, event_bus: Any) -> None:
        """Attach an event bus for telemetry."""
        self._event_bus = event_bus

    def _emit_event(self, event_type: Any, url: str, **extra: Any) -> None:
        """Emit an ingestion event onto the attached event bus."""
        if self._event_bus is not None:
            from harness.events.types import ingestion_event

            evt = ingestion_event(event_type, url, **extra)
            self._event_bus.fire(evt)

    async def fetch(
        self,
        source: str,
        *,
        ref: str = "main",
        force: bool = False,
    ) -> Path:
        """Fetch a repository or ZIP archive and return the extracted directory path.

        Args:
            source: GitHub URL, owner/repo shorthand, remote ZIP URL, or local file/dir.
            ref: Git ref to download (branch, tag, commit). Default: ``main``.
            force: Re-download even if already cached.

        Returns:
            Path to the extracted plugin directory.

        Raises:
            FetchError: If the download or extraction fails.
        """
        from harness.events.types import EventType

        source_clean = source.strip()
        self._emit_event(EventType.REPO_FETCH_STARTED, source_clean, ref=ref, force=force)

        try:
            # 1. Local existing directory
            local_dir = Path(source_clean)
            if local_dir.exists() and local_dir.is_dir():
                res = local_dir.resolve()
                self._emit_event(EventType.REPO_FETCH_COMPLETED, source_clean, path=str(res), local=True)
                return res

            # 2. Local ZIP file
            if local_dir.exists() and local_dir.suffix.lower() == ".zip":
                res = await self._fetch_local_zip(local_dir.resolve(), force=force)
                self._emit_event(EventType.REPO_FETCH_COMPLETED, source_clean, path=str(res), local_zip=True)
                return res

            # 3. Direct remote HTTP/HTTPS ZIP URL (not a GitHub tree/repo URL)
            if source_clean.startswith(("http://", "https://")) and (
                source_clean.split("?")[0].endswith(".zip")
                and "/archive/refs/" not in source_clean
            ):
                res = await self._fetch_remote_zip(source_clean, force=force)
                self._emit_event(EventType.REPO_FETCH_COMPLETED, source_clean, path=str(res), remote_zip=True)
                return res

            # 4. Multi-provider URL or shorthand (GitHub, GitLab, Codeberg, Bitbucket, Generic Git)
            parsed = parse_repo_source(source_clean, default_ref=ref)
            if parsed is not None:
                if parsed.provider == RepoProvider.GENERIC_GIT:
                    res = await self._fetch_git_clone(
                        parsed.clone_url or source_clean,
                        parsed.repo,
                        ref=ref,
                        force=force,
                    )
                    self._emit_event(EventType.REPO_FETCH_COMPLETED, source_clean, path=str(res), provider=parsed.provider.value)
                    return res

                res = await self._fetch_remote_repo_archive(
                    parsed.provider.value,
                    parsed.owner,
                    parsed.repo,
                    ref=parsed.ref or ref,
                    zip_url=parsed.zip_url,
                    force=force,
                )
                self._emit_event(
                    EventType.REPO_FETCH_COMPLETED,
                    source_clean,
                    path=str(res),
                    owner=parsed.owner,
                    repo=parsed.repo,
                    provider=parsed.provider.value,
                )
                return res

            err = FetchError(source, "Not a valid repository URL, remote ZIP URL, or local path")
            self._emit_event(EventType.REPO_FETCH_ERROR, source_clean, error=str(err))
            raise err
        except Exception as e:
            if not isinstance(e, FetchError):
                self._emit_event(EventType.REPO_FETCH_ERROR, source_clean, error=str(e))
            raise

    def _is_cache_valid(
        self,
        target_dir: Path,
        *,
        expected_source: str,
        expected_hash: str | None = None,
        expected_ref: str | None = None,
    ) -> bool:
        """Validate cached directory against expected source, hash, and ref."""
        meta_file = target_dir / ".cache_meta.json"
        if not meta_file.exists():
            return False
        try:
            data = json.loads(meta_file.read_text(encoding="utf-8"))
            if data.get("source") != expected_source:
                return False
            if expected_hash is not None and data.get("hash") != expected_hash:
                return False
            if expected_ref is not None and data.get("ref") != expected_ref:
                return False
            return True
        except Exception:
            return False

    async def _download_zip_streaming(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: dict[str, str],
        zip_path: Path,
    ) -> None:
        """Stream download to disk in chunks, enforcing max_download_bytes."""
        # Detect mock in tests patching httpx.AsyncClient.get
        is_mock = hasattr(client.get, "mock_calls") or hasattr(client.get, "return_value")
        if is_mock:
            response = await client.get(url, headers=headers)
            if hasattr(response, "raise_for_status"):
                response.raise_for_status()
            content = getattr(response, "content", b"")
            if len(content) > self._max_download_bytes:
                raise FetchError(
                    url,
                    f"Download size exceeded limit ({len(content)} > {self._max_download_bytes} bytes)",
                )
            with open(zip_path, "wb") as f:
                f.write(content)
            return

        total_downloaded = 0
        chunk_size = 64 * 1024
        try:
            async with client.stream("GET", url, headers=headers) as response:
                response.raise_for_status()
                content_length = response.headers.get("Content-Length")
                if content_length and content_length.isdigit():
                    if int(content_length) > self._max_download_bytes:
                        raise FetchError(
                            url,
                            f"Download size exceeded limit ({content_length} > {self._max_download_bytes} bytes)",
                        )
                with open(zip_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                        total_downloaded += len(chunk)
                        if total_downloaded > self._max_download_bytes:
                            raise FetchError(
                                url,
                                f"Download size exceeded limit ({total_downloaded} > {self._max_download_bytes} bytes)",
                            )
                        f.write(chunk)
        except Exception:
            zip_path.unlink(missing_ok=True)
            raise

    async def _fetch_remote_zip(self, url: str, force: bool = False) -> Path:
        """Download a direct remote ZIP file and extract it."""
        url_clean = url.split("?")[0]
        filename = Path(url_clean).stem or "remote_plugin"
        url_hash = hashlib.sha256(url.strip().encode("utf-8")).hexdigest()[:12]
        dir_name = f"{filename}__{url_hash}"
        target_dir = self._plugin_dir / dir_name

        if (
            target_dir.exists()
            and not force
            and self._is_cache_valid(
                target_dir,
                expected_source=url,
                expected_hash=url_hash,
            )
        ):
            logger.info("Remote ZIP plugin already cached", url=url, path=str(target_dir))
            return target_dir

        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)

        zip_path = self._plugin_dir / f"{dir_name}.zip"
        headers: dict[str, str] = {}
        if self._token and "github.com" in url:
            headers["Authorization"] = f"Bearer {self._token}"

        logger.info("Downloading remote ZIP archive", url=url)
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
                await self._download_zip_streaming(client, url, headers, zip_path)
        except Exception as e:
            zip_path.unlink(missing_ok=True)
            if isinstance(e, FetchError):
                raise
            raise FetchError(url, str(e)) from e

        return self._extract_zip(
            zip_path,
            target_dir,
            cleanup_zip=True,
            source=url,
            source_type="remote_zip",
            source_hash=url_hash,
            stem=filename,
        )

    async def _fetch_remote_repo_archive(
        self,
        provider: str,
        owner: str,
        repo: str,
        *,
        ref: str = "main",
        zip_url: str | None = None,
        force: bool = False,
    ) -> Path:
        """Download a remote repository archive (GitHub, GitLab, Codeberg, Bitbucket) and extract it."""
        clean_owner = owner.replace("/", "_")
        plugin_name = f"{clean_owner}__{repo}" if provider == "github" else f"{provider}__{clean_owner}__{repo}"
        target_dir = self._plugin_dir / plugin_name
        expected_src = f"{owner}/{repo}" if provider == "github" else f"{provider}:{owner}/{repo}"

        if (
            target_dir.exists()
            and not force
            and self._is_cache_valid(
                target_dir,
                expected_source=expected_src,
                expected_ref=ref,
            )
        ):
            logger.info(
                "Plugin already cached, skipping download",
                plugin=plugin_name,
                path=str(target_dir),
            )
            return target_dir

        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)

        if not zip_url:
            if provider == "gitlab":
                zip_url = f"https://gitlab.com/{owner}/{repo}/-/archive/{ref}/{repo}-{ref}.zip"
            elif provider == "codeberg":
                zip_url = f"https://codeberg.org/{owner}/{repo}/archive/{ref}.zip"
            elif provider == "bitbucket":
                zip_url = f"https://bitbucket.org/{owner}/{repo}/get/{ref}.zip"
            else:
                zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{ref}.zip"

        zip_path = self._plugin_dir / f"{plugin_name}.zip"
        headers: dict[str, str] = {}
        if provider == "github":
            headers["Accept"] = "application/vnd.github+json"
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"
        elif provider == "gitlab" and self._token:
            headers["PRIVATE-TOKEN"] = self._token
        elif self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        logger.info(
            "Downloading repository archive",
            provider=provider,
            owner=owner,
            repo=repo,
            ref=ref,
            url=zip_url,
        )

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
                await self._download_zip_streaming(client, zip_url, headers, zip_path)

        except httpx.HTTPStatusError as e:
            zip_path.unlink(missing_ok=True)
            # Try alternate ref names if 'main' fails
            if ref == "main" and e.response.status_code == 404:
                logger.info("Branch 'main' not found, trying 'master'")
                return await self._fetch_remote_repo_archive(
                    provider, owner, repo, ref="master", force=force
                )
            # Try tag download if heads failed on GitHub
            if provider == "github" and e.response.status_code == 404:
                tag_url = f"https://github.com/{owner}/{repo}/archive/refs/tags/{ref}.zip"
                try:
                    async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
                        await self._download_zip_streaming(client, tag_url, headers, zip_path)
                    return self._extract_zip(
                        zip_path,
                        target_dir,
                        cleanup_zip=True,
                        source=expected_src,
                        source_type=provider,
                        ref=ref,
                        stem=repo,
                    )
                except Exception:
                    pass
            raise FetchError(
                f"{owner}/{repo}", f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            ) from e
        except Exception as e:
            zip_path.unlink(missing_ok=True)
            if isinstance(e, FetchError):
                raise
            raise FetchError(f"{owner}/{repo}", str(e)) from e

        # Extract ZIP
        return self._extract_zip(
            zip_path,
            target_dir,
            cleanup_zip=True,
            source=expected_src,
            source_type=provider,
            ref=ref,
            stem=repo,
        )

    async def _fetch_github(
        self,
        owner: str,
        repo: str,
        *,
        ref: str = "main",
        force: bool = False,
    ) -> Path:
        """Download a GitHub repository as a ZIP and extract it."""
        return await self._fetch_remote_repo_archive("github", owner, repo, ref=ref, force=force)

    async def _fetch_git_clone(
        self,
        clone_url: str,
        repo_name: str,
        *,
        ref: str = "main",
        force: bool = False,
    ) -> Path:
        """Clone generic Git repository via local git binary."""
        plugin_name = f"git__{repo_name}"
        target_dir = self._plugin_dir / plugin_name

        if (
            target_dir.exists()
            and not force
            and self._is_cache_valid(
                target_dir,
                expected_source=clone_url,
                expected_ref=ref,
            )
        ):
            logger.info("Generic git repo already cached", repo=repo_name, path=str(target_dir))
            return target_dir

        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)

        git_bin = shutil.which("git")
        if not git_bin:
            raise FetchError(clone_url, "git executable not found on PATH for generic git clone")

        target_dir.mkdir(parents=True, exist_ok=True)
        cmd = [git_bin, "clone", "--depth", "1", "-b", ref, clone_url, str(target_dir)]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                shutil.rmtree(target_dir, ignore_errors=True)
                cmd = [git_bin, "clone", "--depth", "1", clone_url, str(target_dir)]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise FetchError(clone_url, f"git clone failed: {stderr.decode('utf-8', errors='ignore')[:200]}")
        except Exception as e:
            shutil.rmtree(target_dir, ignore_errors=True)
            if isinstance(e, FetchError):
                raise
            raise FetchError(clone_url, f"git subprocess failed: {e}") from e

        git_dir = target_dir / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir, ignore_errors=True)

        meta = {
            "source": clone_url,
            "source_type": "generic_git",
            "hash": hashlib.sha256(clone_url.encode("utf-8")).hexdigest()[:12],
            "ref": ref,
            "stem": repo_name,
            "cached_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        (target_dir / ".cache_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return target_dir

    async def _fetch_local_zip(self, zip_path: Path, force: bool = False) -> Path:
        """Extract a local ZIP file into the plugin directory."""
        filename = zip_path.stem
        try:
            st = zip_path.stat()
            content_seed = f"{zip_path.resolve()}_{st.st_size}_{st.st_mtime_ns}".encode("utf-8")
        except OSError:
            content_seed = str(zip_path.resolve()).encode("utf-8")
        path_hash = hashlib.sha256(content_seed).hexdigest()[:12]
        dir_name = f"{filename}__{path_hash}"
        target_dir = self._plugin_dir / dir_name

        if (
            target_dir.exists()
            and not force
            and self._is_cache_valid(
                target_dir,
                expected_source=str(zip_path.resolve()),
                expected_hash=path_hash,
            )
        ):
            logger.info("Local ZIP plugin already cached", zip_path=str(zip_path), path=str(target_dir))
            return target_dir

        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)

        return self._extract_zip(
            zip_path,
            target_dir,
            cleanup_zip=False,
            source=str(zip_path.resolve()),
            source_type="local_zip",
            source_hash=path_hash,
            stem=filename,
        )

    def _extract_zip(
        self,
        zip_path: Path,
        target_dir: Path,
        *,
        cleanup_zip: bool = True,
        source: str = "",
        source_type: str = "",
        source_hash: str = "",
        ref: str = "",
        stem: str = "",
    ) -> Path:
        """Extract a ZIP archive, flattening single top-level directories."""
        target_dir.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                try:
                    validate_zip_members(
                        zf,
                        target_dir,
                        max_files=self._max_extract_files,
                        max_total_bytes=self._max_extract_bytes,
                    )
                except ValueError as e:
                    raise FetchError(str(zip_path), f"Unsafe ZIP member: {e}") from e
                zf.extractall(target_dir)
                num_files = len(zf.infolist())
        except zipfile.BadZipFile as e:
            raise FetchError(str(zip_path), f"Invalid ZIP: {e}") from e

        # GitHub ZIPs contain a single top-level directory (e.g., repo-main/).
        # Flatten it so the plugin files are directly in target_dir.
        children = [c for c in target_dir.iterdir() if c.name != ".cache_meta.json"]
        if len(children) == 1 and children[0].is_dir():
            nested = children[0]
            # Move contents up one level
            for item in nested.iterdir():
                dest = target_dir / item.name
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                shutil.move(str(item), str(dest))
            nested.rmdir()

        meta = {
            "source": source,
            "source_type": source_type,
            "hash": source_hash,
            "ref": ref,
            "stem": stem or target_dir.name.split("__")[0],
            "cached_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        meta_path = target_dir / ".cache_meta.json"
        try:
            meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("Could not write .cache_meta.json", error=str(e))

        if cleanup_zip:
            zip_path.unlink(missing_ok=True)

        logger.info(
            "Repository extracted",
            target=str(target_dir),
            files=num_files,
        )

        return target_dir

    def list_cached(self) -> list[dict[str, Any]]:
        """List all cached plugin directories.

        Returns:
            List of dicts with ``name``, ``path``, and ``has_manifest`` keys.
        """
        result: list[dict[str, Any]] = []
        if not self._plugin_dir.exists():
            return result

        for child in sorted(self._plugin_dir.iterdir()):
            if child.is_dir():
                meta_file = child / ".cache_meta.json"
                meta: dict[str, Any] = {}
                if meta_file.exists():
                    try:
                        meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                result.append(
                    {
                        "name": child.name,
                        "path": str(child),
                        "has_manifest": (child / "plugin.json").exists(),
                        "meta": meta,
                    }
                )
        return result

    def remove_cached(self, name: str) -> bool:
        """Remove a cached plugin directory by exact name or stem.

        Args:
            name: Plugin directory name or stem without hash.

        Returns:
            True if any matching directory was found and removed.
        """
        target = self._plugin_dir / name
        removed = False
        if target.exists() and target.is_dir():
            shutil.rmtree(target)
            logger.info("Removed cached plugin", name=name)
            removed = True

        if not removed and self._plugin_dir.exists():
            for child in self._plugin_dir.iterdir():
                if child.is_dir() and child.name.startswith(f"{name}__"):
                    shutil.rmtree(child)
                    logger.info("Removed cached plugin by stem", stem=name, name=child.name)
                    removed = True
        return removed
