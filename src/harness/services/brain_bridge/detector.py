"""Format detection and remote git repository cloning for Brain Bridge."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def is_git_url(path_or_url: str) -> bool:
    """Check if the given string is a remote Git repository URL."""
    low = path_or_url.strip().lower()
    if low.startswith(("http://", "https://", "git@", "git://", "ssh://")):
        return True
    if low.endswith(".git"):
        return True
    return False


def detect_brain_format(root: Path) -> str:
    """Detect format of the external brain, repository, or knowledge store."""
    if (root / ".system_generated" / "logs").exists() or (root / "transcript.jsonl").exists():
        return "antigravity_brain"
    if any(root.glob("**/transcript.jsonl")):
        return "antigravity_brain"
    if (root / ".harness").exists() or (root / "src" / "harness").exists():
        return "harness_instance"
    if (root / ".claude").exists() or (root / ".cursor").exists() or (root / ".cursorrules").exists():
        return "ide_memo"
    if (root / ".obsidian").exists():
        return "obsidian_vault"
    if (root / ".git").exists():
        return "git_repository"

    md_files = list(root.glob("*.md"))[:10]
    for md in md_files:
        try:
            content = md.read_text(encoding="utf-8", errors="ignore")
            if "[[" in content and "]]" in content:
                return "obsidian_vault"
        except (OSError, UnicodeDecodeError):
            pass

    manifest_markers = ["pyproject.toml", "package.json", "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "CMakeLists.txt"]
    if any((root / marker).exists() for marker in manifest_markers):
        return "git_repository"
    return "raw_docs"


def clone_remote_repo(url: str, alias: str) -> tuple[Path | None, str | None]:
    """Clone a remote git repository into the local cache directory."""
    if not shutil.which("git"):
        return None, "git executable not found in PATH"

    cache_dir = Path.home() / ".harness" / "cache" / "repos" / alias
    cache_dir.parent.mkdir(parents=True, exist_ok=True)

    if cache_dir.exists():
        try:
            pull_res = subprocess.run(
                ["git", "-C", str(cache_dir), "pull"],
                capture_output=True,
                text=True,
                check=False,
            )
            if pull_res.returncode == 0:
                return cache_dir, None
        except Exception:
            pass

    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir, ignore_errors=True)
        except Exception:
            pass

    try:
        clone_proc = subprocess.run(
            ["git", "clone", "--depth", "50", url, str(cache_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        if clone_proc.returncode != 0:
            return None, f"Git clone failed: {clone_proc.stderr.strip()}"
        return cache_dir, None
    except Exception as exc:
        return None, f"Failed to clone repository: {exc}"
