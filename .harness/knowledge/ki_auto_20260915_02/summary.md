# Bounded Directory Traversal & Deep-Scan Hygiene

## Executive Summary
This Knowledge Item establishes the directory traversal and file scanner hygiene standards required for large repository audits, peer project discovery, and background tasks.

## Failure Mode Analysis
In session `ce123a13-154f-4977-8ed2-47dd1206a76f`, a background task executing `check_peer_projects.py` performed an unpruned recursive directory walk (`Path.rglob("*")`) across sibling repositories. This caused:
- Deep traversal into nested `.git/objects/`, `node_modules/`, and `.venv/` hierarchies containing tens of thousands of binary and temporary files.
- Process stalling and pipe buffer saturation.
- Task cancellation after timeout (Task-53 killed at step 57).

## Mandatory Traversal Hygiene (Rule 52)
1. **Noise Directory Pruning**:
   Directory scanners must actively exclude:
   `PRUNE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "target", "dist", "build", ".gemini", ".pytest_cache"}`
2. **Maximum Scan Depth Bounds**:
   Directory walking algorithms must maintain a depth counter and terminate recursion at depth $\le 4$.
3. **Breadth-First Exploration**:
   Inspect top-level manifests (`pyproject.toml`, `package.json`, `Cargo.toml`) before descending into package source trees.
4. **Timeout Guards**:
   Asynchronous subprocess runners must specify explicit timeouts (e.g. 15-30 seconds for local scans).

## Verification
- Validated against Brain Harness Rule 52.
