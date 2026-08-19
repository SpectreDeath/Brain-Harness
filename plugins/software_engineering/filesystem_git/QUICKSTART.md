# Quick Start Guide: `plugin.filesystem_git` (v1.0.0)

> Safe filesystem navigation, line-slice reading, regex search, and git operations

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`fs_read_file`**: Read file content with optional start_line and end_line slicing (1-indexed)
- **`fs_write_file`**: Write or overwrite text content to a file
- **`fs_list_dir`**: List files and directories in a directory with file sizes and directory item counts
- **`fs_search_text`**: Search text or regex pattern across files in directory
- **`git_status`**: Get git repository status (staged, modified, untracked files, current branch)
- **`git_diff`**: Get git diff for uncommitted changes or against a commit/branch
- **`git_log`**: Get recent git commit log

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('plugin.filesystem_git.fs_read_file', {'path': '<path>', 'start_line': '<start_line>', 'end_line': '<end_line>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider plugin.filesystem_git
harness plugin enable plugin.filesystem_git
```

## ⚡ Available Entrypoints & Skills
- **`fs_read_file(path: string, start_line: integer, end_line: integer)`**
  Read file content with optional start_line and end_line slicing (1-indexed)
- **`fs_write_file(path: string, content: string, overwrite: boolean)`**
  Write or overwrite text content to a file
- **`fs_list_dir(path: string, max_depth: integer)`**
  List files and directories in a directory with file sizes and directory item counts
- **`fs_search_text(pattern: string, search_path: string, case_sensitive: boolean)`**
  Search text or regex pattern across files in directory
- **`git_status(repo_path: string)`**
  Get git repository status (staged, modified, untracked files, current branch)
- **`git_diff(repo_path: string, target: string)`**
  Get git diff for uncommitted changes or against a commit/branch
- **`git_log(repo_path: string, max_commits: integer)`**
  Get recent git commit log