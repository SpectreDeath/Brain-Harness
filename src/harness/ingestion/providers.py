"""Repository source providers and URL resolution for universal ingestion.

Supports GitHub, GitLab, Codeberg, Bitbucket, and generic Git repositories.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class RepoProvider(str, Enum):
    """Supported repository hosting providers."""

    GITHUB = "github"
    GITLAB = "gitlab"
    CODEBERG = "codeberg"
    BITBUCKET = "bitbucket"
    GENERIC_GIT = "generic_git"
    LOCAL_ZIP = "local_zip"
    LOCAL_DIR = "local_dir"
    REMOTE_ZIP = "remote_zip"


@dataclass(slots=True, frozen=True)
class ParsedRepoSource:
    """Structured information extracted from a repository source string."""

    provider: RepoProvider
    owner: str
    repo: str
    ref: str
    zip_url: str | None = None
    clone_url: str | None = None


# --- URL Matching Regular Expressions ---
_GITHUB_TREE_RE = re.compile(r"^(?:https?://github\.com/)?([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)/tree/([a-zA-Z0-9_./-]+)/?$")
_GITHUB_ARCHIVE_RE = re.compile(r"^(?:https?://github\.com/)?([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)/archive/refs/(?:heads|tags)/([a-zA-Z0-9_./-]+?)(?:\.zip)?/?$")
_GITHUB_SSH_RE = re.compile(r"^git@github\.com:([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?$")
_GITHUB_URL_RE = re.compile(r"^(?:https?://github\.com/)?([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?/?$")

_GITLAB_TREE_RE = re.compile(r"^https?://gitlab\.com/([a-zA-Z0-9_./-]+?)/-/tree/([a-zA-Z0-9_./-]+)/?$")
_GITLAB_ARCHIVE_RE = re.compile(r"^https?://gitlab\.com/([a-zA-Z0-9_./-]+?)/-/archive/([a-zA-Z0-9_./-]+?)/.+?\.zip$")
_GITLAB_SSH_RE = re.compile(r"^git@gitlab\.com:([a-zA-Z0-9_./-]+?)(?:\.git)?$")
_GITLAB_URL_RE = re.compile(r"^https?://gitlab\.com/([a-zA-Z0-9_./-]+?)(?:\.git)?/?$")

_CODEBERG_TREE_RE = re.compile(r"^https?://codeberg\.org/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)/src/(?:branch|tag)/([a-zA-Z0-9_./-]+)/?$")
_CODEBERG_ARCHIVE_RE = re.compile(r"^https?://codeberg\.org/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)/archive/([a-zA-Z0-9_./-]+?)(?:\.zip)?/?$")
_CODEBERG_SSH_RE = re.compile(r"^git@codeberg\.org:([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?$")
_CODEBERG_URL_RE = re.compile(r"^https?://codeberg\.org/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?/?$")

_BITBUCKET_TREE_RE = re.compile(r"^https?://bitbucket\.org/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)/src/([a-zA-Z0-9_./-]+)/?$")
_BITBUCKET_SSH_RE = re.compile(r"^git@bitbucket\.org:([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?$")
_BITBUCKET_URL_RE = re.compile(r"^https?://bitbucket\.org/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?/?$")

_GENERIC_GIT_SSH_RE = re.compile(r"^git@[a-zA-Z0-9_.-]+:(?:[a-zA-Z0-9_.-]+/)*([a-zA-Z0-9_.-]+?)(?:\.git)?$")
_GENERIC_GIT_URL_RE = re.compile(r"^https?://[a-zA-Z0-9_.:-]+/(?:.+/)?([a-zA-Z0-9_.-]+?)\.git$")


def _split_gitlab_path(full_path: str) -> tuple[str, str]:
    """Split GitLab group/subgroup/project path into (namespace, project)."""
    parts = full_path.strip("/").split("/")
    if len(parts) == 1:
        return parts[0], parts[0]
    return "/".join(parts[:-1]), parts[-1]


def parse_repo_source(source: str, default_ref: str = "main") -> ParsedRepoSource | None:
    """Parse repository source string into a ParsedRepoSource."""
    s = source.strip()

    # 1. GitLab
    m = _GITLAB_TREE_RE.match(s)
    if m:
        ns, proj = _split_gitlab_path(m.group(1))
        ref = m.group(2)
        return ParsedRepoSource(
            RepoProvider.GITLAB, ns, proj, ref,
            zip_url=f"https://gitlab.com/{m.group(1)}/-/archive/{ref}/{proj}-{ref}.zip",
            clone_url=f"https://gitlab.com/{m.group(1)}.git",
        )
    m = _GITLAB_ARCHIVE_RE.match(s)
    if m:
        ns, proj = _split_gitlab_path(m.group(1))
        ref = m.group(2)
        return ParsedRepoSource(RepoProvider.GITLAB, ns, proj, ref, zip_url=s, clone_url=f"https://gitlab.com/{m.group(1)}.git")
    m = _GITLAB_SSH_RE.match(s) or _GITLAB_URL_RE.match(s)
    if m:
        ns, proj = _split_gitlab_path(m.group(1))
        return ParsedRepoSource(
            RepoProvider.GITLAB, ns, proj, default_ref,
            zip_url=f"https://gitlab.com/{m.group(1)}/-/archive/{default_ref}/{proj}-{default_ref}.zip",
            clone_url=f"https://gitlab.com/{m.group(1)}.git",
        )

    # 2. Codeberg
    m = _CODEBERG_TREE_RE.match(s)
    if m:
        owner, repo, ref = m.group(1), m.group(2), m.group(3)
        return ParsedRepoSource(
            RepoProvider.CODEBERG, owner, repo, ref,
            zip_url=f"https://codeberg.org/{owner}/{repo}/archive/{ref}.zip",
            clone_url=f"https://codeberg.org/{owner}/{repo}.git",
        )
    m = _CODEBERG_ARCHIVE_RE.match(s)
    if m:
        owner, repo, ref = m.group(1), m.group(2), m.group(3)
        return ParsedRepoSource(RepoProvider.CODEBERG, owner, repo, ref, zip_url=s, clone_url=f"https://codeberg.org/{owner}/{repo}.git")
    m = _CODEBERG_SSH_RE.match(s) or _CODEBERG_URL_RE.match(s)
    if m:
        owner, repo = m.group(1), m.group(2)
        return ParsedRepoSource(
            RepoProvider.CODEBERG, owner, repo, default_ref,
            zip_url=f"https://codeberg.org/{owner}/{repo}/archive/{default_ref}.zip",
            clone_url=f"https://codeberg.org/{owner}/{repo}.git",
        )

    # 3. Bitbucket
    m = _BITBUCKET_TREE_RE.match(s)
    if m:
        owner, repo, ref = m.group(1), m.group(2), m.group(3)
        return ParsedRepoSource(
            RepoProvider.BITBUCKET, owner, repo, ref,
            zip_url=f"https://bitbucket.org/{owner}/{repo}/get/{ref}.zip",
            clone_url=f"https://bitbucket.org/{owner}/{repo}.git",
        )
    m = _BITBUCKET_SSH_RE.match(s) or _BITBUCKET_URL_RE.match(s)
    if m:
        owner, repo = m.group(1), m.group(2)
        return ParsedRepoSource(
            RepoProvider.BITBUCKET, owner, repo, default_ref,
            zip_url=f"https://bitbucket.org/{owner}/{repo}/get/{default_ref}.zip",
            clone_url=f"https://bitbucket.org/{owner}/{repo}.git",
        )

    # 4. GitHub
    m = _GITHUB_TREE_RE.match(s)
    if m:
        owner, repo, ref = m.group(1), m.group(2), m.group(3)
        return ParsedRepoSource(
            RepoProvider.GITHUB, owner, repo, ref,
            zip_url=f"https://github.com/{owner}/{repo}/archive/refs/heads/{ref}.zip",
            clone_url=f"https://github.com/{owner}/{repo}.git",
        )
    m = _GITHUB_ARCHIVE_RE.match(s)
    if m:
        owner, repo, ref = m.group(1), m.group(2), m.group(3)
        return ParsedRepoSource(RepoProvider.GITHUB, owner, repo, ref, zip_url=s, clone_url=f"https://github.com/{owner}/{repo}.git")
    m = _GITHUB_SSH_RE.match(s) or _GITHUB_URL_RE.match(s)
    if m:
        owner, repo = m.group(1), m.group(2)
        return ParsedRepoSource(
            RepoProvider.GITHUB, owner, repo, default_ref,
            zip_url=f"https://github.com/{owner}/{repo}/archive/refs/heads/{default_ref}.zip",
            clone_url=f"https://github.com/{owner}/{repo}.git",
        )

    # 5. Generic Git Repository
    m = _GENERIC_GIT_SSH_RE.match(s) or _GENERIC_GIT_URL_RE.match(s)
    if m:
        repo_name = m.group(1)
        return ParsedRepoSource(
            RepoProvider.GENERIC_GIT, "generic", repo_name, default_ref,
            zip_url=None, clone_url=s,
        )

    return None
