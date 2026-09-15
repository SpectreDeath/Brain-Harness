# plugin.filesystem_git (v1.0.0)

Safe filesystem navigation, line-slice reading, regex search, and git operations

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/software_engineering/filesystem_git` |
| Category | `software_engineering` |
| Isolation Mode | `in_process` |
| Services Provided | `service.filesystem_git` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `fs_read_file` | `(path, start_line, end_line)` | Read file content with optional start_line and end_line slicing (1-indexed) |
| `fs_write_file` | `(path, content, overwrite)` | Write or overwrite text content to a file |
| `fs_list_dir` | `(path, max_depth)` | List files and directories in a directory with file sizes and directory item counts |
| `fs_search_text` | `(pattern, search_path, case_sensitive)` | Search text or regex pattern across files in directory |
| `git_status` | `(repo_path)` | Get git repository status (staged, modified, untracked files, current branch) |
| `git_diff` | `(repo_path, target)` | Get git diff for uncommitted changes or against a commit/branch |
| `git_log` | `(repo_path, max_commits)` | Get recent git commit log |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Filesystem & Git tools for Brain Harness autonomous agents.

#### Classes

- `class FilesystemGitPlugin` — Harness Plugin providing filesystem operations and Git integration.
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def read_file(path, start_line, end_line) -> FileReadResult`
  - `def write_file(path, content, overwrite) -> FileWriteResult`
  - `def list_dir(path, max_depth) -> DirListResult`
  - `def search_text(pattern, search_path, case_sensitive) -> SearchResult`
  - `def git_status(repo_path) -> GitStatusResult`
  - `def git_diff(repo_path, target) -> GitDiffResult`
  - `def git_log(repo_path, max_commits) -> GitLogResult`


#### Functions

- `def fs_read_file(path, start_line, end_line) -> dict[str, Any]` — Read file content with optional line-slice.
- `def fs_write_file(path, content, overwrite) -> dict[str, Any]` — Write or overwrite text content to a file.
- `def fs_list_dir(path, max_depth) -> dict[str, Any]` — List directory contents recursively up to max_depth.
- `def fs_search_text(pattern, search_path, case_sensitive) -> dict[str, Any]` — Search for pattern across text files.
- `def git_status(repo_path) -> dict[str, Any]` — Get status of the git repository.
- `def git_diff(repo_path, target) -> dict[str, Any]` — Get git diff.
- `def git_log(repo_path, max_commits) -> dict[str, Any]` — Get git commit history.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.software_engineering.filesystem_git.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
