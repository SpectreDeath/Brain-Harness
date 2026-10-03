# Privilege-Aware Posix Cgroup v2 Isolation & Hierarchical Slice Traversal

## Problem
When sandboxing subprocesses on Linux environments:
1. Modern Linux distributions enforce unified cgroup v2 hierarchies. Applying resource limits to root cgroups (`/sys/fs/cgroup/`) requires root permissions (`sudo` or `CAP_SYS_ADMIN`), which are unavailable in standard container sandboxes, non-root systemd sessions, or CI runners.
2. Attempting to write directly to root `memory.max` triggers `PermissionError: [Errno 13] Permission denied`, causing sandbox initialization to abort.

## Solution
1. **Dynamic User Slice Traversal**:
   - Inspect `/proc/self/cgroup` to discover the active relative slice (e.g. `0::/user.slice/user-1000.slice/...`).
   - Validate delegated controllers by checking `cgroup.controllers` for `memory` and `pids`.
2. **Ephemeral Child Cgroup Provisioning**:
   - Create an ephemeral sub-cgroup under the user's slice (`user.slice/user-1000.slice/harness-subproc-<pid>/`).
   - Set limits cleanly via `memory.max` and add the subprocess PID via `cgroup.procs`.
3. **Graceful Teardown & Cross-Platform Parity**:
   - On subprocess completion or crash, remove the temporary cgroup directory.
   - If cgroups are not mounted or user slice is not writable, fall back gracefully to software RSS polling without crashing the host process.

## Operational Guideline
- Always inspect `/proc/self/cgroup` before attempting cgroup v2 operations.
- Clean up ephemeral cgroup directories during transport teardown to avoid resource leaks.
- Test cgroup lifecycle against `test_posix_cgroup_lifecycle`.

## Provenance
- Source code: `src/harness/plugins/sandbox.py`
- Test contract: `tests/test_sandbox.py::test_posix_cgroup_lifecycle`
- Verification: 42/42 tests passing
