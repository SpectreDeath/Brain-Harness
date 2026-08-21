"""Repo fetcher — downloads GitHub repositories for plugin ingestion.

Supports:
    - Full GitHub URLs (https://github.com/owner/repo)
    - Short-form owner/repo
    - Local ZIP file paths
    - Branch/tag specification
"""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path
from typing import Any

import httpx
import structlog

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


class FetchError(Exception):
    """Raised when fetching a repository fails."""

    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to fetch {url!r}: {reason}")


class RepoFetcher:
    """Downloads GitHub repositories and ZIP archives for plugin ingestion.

    Caches downloads by repository name to avoid redundant fetches.
    """

    def __init__(
        self,
        plugin_dir: Path | None = None,
        *,
        github_token: str | None = None,
        event_bus: Any | None = None,
    ) -> None:
        """Initialize the fetcher.

        Args:
            plugin_dir: Directory to store fetched plugins.
                Defaults to ``~/.harness/plugins/``.
            github_token: Optional GitHub personal access token for
                private repos or higher rate limits.
            event_bus: Optional event bus for ingestion telemetry.
        """
        self._plugin_dir = plugin_dir or DEFAULT_PLUGIN_DIR
        self._plugin_dir.mkdir(parents=True, exist_ok=True)
        self._token = github_token
        self._event_bus = event_bus

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
                res = await self._fetch_local_zip(local_dir.resolve())
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

            # 4. GitHub Tree URL (e.g. https://github.com/owner/repo/tree/my-branch)
            tree_match = _GITHUB_TREE_RE.match(source_clean)
            if tree_match:
                owner, repo, tree_ref = tree_match.group(1), tree_match.group(2), tree_match.group(3)
                effective_ref = tree_ref if ref == "main" else ref
                res = await self._fetch_github(owner, repo, ref=effective_ref, force=force)
                self._emit_event(EventType.REPO_FETCH_COMPLETED, source_clean, path=str(res), owner=owner, repo=repo)
                return res

            # 5. GitHub Archive URL (e.g. https://github.com/owner/repo/archive/refs/tags/v1.0.zip)
            archive_match = _GITHUB_ARCHIVE_RE.match(source_clean)
            if archive_match:
                owner, repo, archive_ref = archive_match.group(1), archive_match.group(2), archive_match.group(3)
                effective_ref = archive_ref if ref == "main" else ref
                res = await self._fetch_github(owner, repo, ref=effective_ref, force=force)
                self._emit_event(EventType.REPO_FETCH_COMPLETED, source_clean, path=str(res), owner=owner, repo=repo)
                return res

            # 6. GitHub SSH URL (e.g. git@github.com:owner/repo.git)
            ssh_match = _GITHUB_SSH_RE.match(source_clean)
            if ssh_match:
                owner, repo = ssh_match.group(1), ssh_match.group(2)
                res = await self._fetch_github(owner, repo, ref=ref, force=force)
                self._emit_event(EventType.REPO_FETCH_COMPLETED, source_clean, path=str(res), owner=owner, repo=repo)
                return res

            # 7. Standard GitHub URL or owner/repo shorthand
            match = _GITHUB_URL_RE.match(source_clean)
            if match:
                owner, repo = match.group(1), match.group(2)
                res = await self._fetch_github(owner, repo, ref=ref, force=force)
                self._emit_event(EventType.REPO_FETCH_COMPLETED, source_clean, path=str(res), owner=owner, repo=repo)
                return res

            err = FetchError(source, "Not a valid GitHub URL, remote ZIP URL, or local path")
            self._emit_event(EventType.REPO_FETCH_ERROR, source_clean, error=str(err))
            raise err
        except Exception as e:
            if not isinstance(e, FetchError):
                self._emit_event(EventType.REPO_FETCH_ERROR, source_clean, error=str(e))
            raise

    async def _fetch_remote_zip(self, url: str, force: bool = False) -> Path:
        """Download a direct remote ZIP file and extract it."""
        url_clean = url.split("?")[0]
        filename = Path(url_clean).stem or "remote_plugin"
        target_dir = self._plugin_dir / filename

        if target_dir.exists() and not force:
            logger.info("Remote ZIP plugin already cached", url=url, path=str(target_dir))
            return target_dir

        zip_path = self._plugin_dir / f"{filename}.zip"
        headers: dict[str, str] = {}
        if self._token and "github.com" in url:
            headers["Authorization"] = f"Bearer {self._token}"

        logger.info("Downloading remote ZIP archive", url=url)
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                with open(zip_path, "wb") as f:  # noqa: ASYNC230
                    f.write(response.content)
        except Exception as e:
            raise FetchError(url, str(e)) from e

        return self._extract_zip(zip_path, target_dir, cleanup_zip=True)

    async def _fetch_github(
        self,
        owner: str,
        repo: str,
        *,
        ref: str = "main",
        force: bool = False,
    ) -> Path:
        """Download a GitHub repository as a ZIP and extract it."""
        plugin_name = f"{owner}__{repo}"
        target_dir = self._plugin_dir / plugin_name

        if target_dir.exists() and not force:
            logger.info(
                "Plugin already cached, skipping download",
                plugin=plugin_name,
                path=str(target_dir),
            )
            return target_dir

        # Download ZIP from GitHub API
        zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{ref}.zip"
        zip_path = self._plugin_dir / f"{plugin_name}.zip"

        headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        logger.info(
            "Downloading repository",
            owner=owner,
            repo=repo,
            ref=ref,
            url=zip_url,
        )

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
                response = await client.get(zip_url, headers=headers)
                response.raise_for_status()

                with open(zip_path, "wb") as f:  # noqa: ASYNC230
                    f.write(response.content)

        except httpx.HTTPStatusError as e:
            # Try alternate ref names if 'main' fails
            if ref == "main" and e.response.status_code == 404:
                logger.info("Branch 'main' not found, trying 'master'")
                return await self._fetch_github(owner, repo, ref="master", force=force)
            # Try tag download if heads failed
            if e.response.status_code == 404:
                tag_url = f"https://github.com/{owner}/{repo}/archive/refs/tags/{ref}.zip"
                try:
                    async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
                        resp_tag = await client.get(tag_url, headers=headers)
                        resp_tag.raise_for_status()
                        with open(zip_path, "wb") as f:  # noqa: ASYNC230
                            f.write(resp_tag.content)
                        return self._extract_zip(zip_path, target_dir, cleanup_zip=True)
                except Exception:
                    pass
            raise FetchError(
                f"{owner}/{repo}", f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            ) from e
        except httpx.RequestError as e:
            raise FetchError(f"{owner}/{repo}", str(e)) from e

        # Extract ZIP
        return self._extract_zip(zip_path, target_dir, cleanup_zip=True)

    async def _fetch_local_zip(self, zip_path: Path) -> Path:
        """Extract a local ZIP file into the plugin directory."""
        plugin_name = zip_path.stem
        target_dir = self._plugin_dir / plugin_name

        return self._extract_zip(zip_path, target_dir, cleanup_zip=False)

    def _extract_zip(
        self,
        zip_path: Path,
        target_dir: Path,
        *,
        cleanup_zip: bool = True,
    ) -> Path:
        """Extract a ZIP archive, flattening single top-level directories."""
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(target_dir)
        except zipfile.BadZipFile as e:
            raise FetchError(str(zip_path), f"Invalid ZIP: {e}") from e

        # GitHub ZIPs contain a single top-level directory (e.g., repo-main/).
        # Flatten it so the plugin files are directly in target_dir.
        children = list(target_dir.iterdir())
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

        if cleanup_zip:
            zip_path.unlink(missing_ok=True)

        logger.info(
            "Repository extracted",
            target=str(target_dir),
            files=len(list(target_dir.rglob("*"))),
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

        for child in self._plugin_dir.iterdir():
            if child.is_dir():
                result.append(
                    {
                        "name": child.name,
                        "path": str(child),
                        "has_manifest": (child / "plugin.json").exists(),
                    }
                )
        return result

    def remove_cached(self, name: str) -> bool:
        """Remove a cached plugin directory.

        Args:
            name: Plugin directory name.

        Returns:
            True if the directory was found and removed.
        """
        target = self._plugin_dir / name
        if target.exists() and target.is_dir():
            shutil.rmtree(target)
            logger.info("Removed cached plugin", name=name)
            return True
        return False
