# Two-Tier Guest Path Virtualization with Traversal Clipping

## Context
When models interact with workspace files, leaking host machine absolute paths (e.g. `C:\Users\username\projects\...` or `/home/user/repo`) pollutes LLM context, breaks deterministic prompt caching across distributed workers, and creates security risks if relative path traversals (`../../`) access sensitive parent directories.

## Distilled Learning
Implement a bidirectional two-tier path virtualization layer:
- **Canonical Model View (`VISIBLE_ROOT`)**: The model always observes and targets clean virtual paths anchored at `/workspace` (with legacy support for `/workspace/artifacts`).
- **Real Session Root (`real_root`)**: In the host or container environment, the path resolves to an isolated guest session tree (e.g. `/workspace/<conversation_id>` or host target directory).
- **Parent Traversal Clipping**: Any `..` traversal attempt that walks out of `/workspace`, `/workspace/artifacts`, or the session root is deterministically clipped to `real_root` instead of escaping to host root directories.
- **Selective Absolute Passthrough**: Legitimate non-workspace system absolutes (e.g. `/tmp`, `/dev/null`) remain untouched while relative paths are safely normalized.

## Triggers & Seam Choices
- **Trigger**: Multi-session agent execution, containerized runners, or distributed remote agent workers.
- **Seam Choice**: Integrate at the workspace bridge layer (`harness.services.workspace` or `xai-grok-workspace`) intercepting inbound tool parameters and outbound observations.
