# How-To: Drive Repositories with Agent Dock

An **Agent Dock** is a repository-level declarative workstation port (`dock.yaml`) that tells an autonomous AI agent how to plug into a repository and drive it from the inside.

Just like a physical workstation dock connects power, displays, networks, and peripherals through a single cable, an Agent Dock provides one unified declaration of runnable procedures, exposed tools, capability permissions, and safety boundaries.

---

## 1. Core Architecture & Conceptual Distinction

An Agent Dock sits at the repository level. It is distinct from both plugins and bridges:

| Concept | Scope | Declaration File | Responsibility |
| :--- | :--- | :--- | :--- |
| **Plugin** | Micro-Kernel Capability | `plugins/<cat>/<name>/plugin.json` | Registers tools, models, or storage implementations into the IoC container. |
| **Bridge** | Cross-System Protocol | `src/harness/bridges/` | Translates protocols between external orchestrators and the harness micro-kernel. |
| **Agent Dock** | Repository Workstation Port | Repo-root `dock.yaml` | Declares how an agent drives a specific codebase: procedures, boundaries, permissions, and tool surface. |

Discovering a dock parses YAML data without executing any repository code (`read without running`). Driving a dock requires explicit human-in-the-loop approval of the manifest SHA-256 digest and enforces hard safety boundaries before spawning subprocesses.

---

## 2. The `dock.yaml` Specification

A repository declares its dock in repo-root `dock.yaml`. The schema uses sequential procedures and explicit capability flags:

```yaml
name: brain-harness
description: "Brain Harness agent dock — workstation port for inspecting, testing, and driving the micro-kernel"
version: "0.1.0"

permissions:
  read: true
  run: true
  write: true
  push: false

boundaries:
  paths:
    - ".git/"
    - ".env"
    - ".pytest_cache/"
    - "src/harness/ui/static/"
  operations:
    - "git push --force"
    - "git reset --hard"
    - "git clean -fd"

tools:
  - "fs_read_file"
  - "fs_search_text"
  - "fs_git_status"
  - "fs_git_diff"
  - "run_pytest"

entrypoints:
  vault-stats:
    description: "Display knowledge graph and vault statistics"
    write_path: false
    steps:
      - command: "python src/harness/cli.py knowledge stats"
        workdir: "."
        expected_output: "Active Knowledge Items"

  verify-core:
    description: "Run targeted dock verification tests"
    write_path: false
    steps:
      - command: "pytest tests/test_service_dock.py tests/test_command_dock.py -v"
        workdir: "."

  sync-context:
    description: "Lint and verify codebase context and instruction file hygiene"
    write_path: true
    steps:
      - command: "python src/harness/cli.py context lint --root ."
        workdir: "."
```

### Schema Fields

- `name` (string, required): Unique identifier for the repository dock.
- `description` (string, required): Human-readable purpose of the dock.
- `permissions` (mapping):
  - `read` (bool, default `true`): Permission to inspect files and git status.
  - `run` (bool, default `true`): Permission to execute declared procedures.
  - `write` (bool, default `false`): Permission to execute `write_path: true` procedures.
  - `push` (bool, default `false`): Permission to execute non-force `git push` commands.
- `boundaries` (mapping):
  - `paths` (list of strings): Off-limits paths. Any command referencing these paths is refused before execution.
  - `operations` (list of strings): Prohibited command patterns (e.g. `git push --force`, `git reset --hard`).
- `tools` (list of strings): Named tool identifiers exposed to the agent or operator.
- `entrypoints` (mapping): Named procedures containing sequential steps.
  - `description` (string): Procedure documentation.
  - `write_path` (bool, default `false`): Flags whether procedure modifies files.
  - `steps` (list): Ordered execution steps. Each step defines either:
    - `command`: Command string to execute in a subprocess.
    - `workdir`: Working directory relative to repository root (defaults to `.`, strictly confined).
    - `expected_output`: Optional substring assertion in stdout.
    - Or `call_procedure`: Name of another procedure to call (cycle-safe, max depth 5).

---

## 3. Generic Dock Fallback

When linking to a repository that lacks a `dock.yaml`, the harness synthesizes a deterministic **Generic Dock** (`declared: false`):

- **Auto-detected procedures**: Automatically exposes `test` (detecting `pytest`, Node test runners, or `cargo test` from manifest files) and `status` (`git status --short`).
- **Safe default boundaries**: Prohibits touching `.git/`, `.env`, `.pytest_cache/`, `src/harness/ui/static/`, and blocks `git push --force`, `git reset --hard`, and `git clean -fd`.
- **Default permissions**: Read-only (`read: true, run: true, write: false, push: false`).

---

## 4. CLI Workflow

All dock operations are exposed via `harness dock`:

### Inspecting a Dock
Inspect a local directory or remote repository without linking or modifying state:

```bash
harness dock inspect .
harness dock inspect . --json
```

### Linking with Approval Digest
Link an agent dock to your active harness workspace:

```bash
# Interactive prompt
harness dock link .

# Non-interactive / CI with explicit approval
harness dock link . --name brain-harness --approve
```

The approval stores the SHA-256 digest of `dock.yaml` in `.harness/docks.json`.

### Listing Linked Docks
View all linked docks and verify whether manifest drift has occurred:

```bash
harness dock list
```

Status indicates:
- `approved`: Manifest matches the recorded approval SHA-256 digest.
- `manifest_changed`: `dock.yaml` was modified after link time. Execution is blocked until re-linked with `--approve`.
- `unapproved`: Linked without operator approval.

### Listing Exposed Tools
```bash
harness dock tools brain-harness
```
*Note: Tools listed by `harness dock tools` represent declared capabilities advertised by the dock manifest (unverified against the host `ToolRegistry`).*

### Running Procedures
Execute a declared procedure on a linked dock:

```bash
# Dry-run inspection
harness dock run brain-harness verify-core --dry-run

# Real execution
harness dock run brain-harness verify-core
```

---

## 5. Trust, Permissions, and Boundaries

The Agent Dock security model adheres to strict invariants:

1. **Who Declares**: The repository owner authors `dock.yaml`.
2. **Who Approves**: The human operator connecting the agent approves the manifest digest and visible procedure commands at `harness dock link` time.
3. **Digest Pinning**: Any modification to `dock.yaml` (or synthesized manifest in generic docks) invalidates approval and raises `DockApprovalDriftError` on `harness dock run` until re-approved.
4. **Pre-Execution Refusal & Workdir Confinement**: Boundaries are enforced *before* execution. Each step process is strictly confined to its resolved `workdir` relative to the repository root. Steps referencing a boundary path token, matching a forbidden operation pattern, or attempting directory traversal (`../`) outside the repository tree are refused before subprocess creation. Boundary enforcement guarantees process workdir confinement rather than full semantic regex sanitization of all arbitrary CLI flags.
5. **Credential Scrubbing**: Dock procedures never receive credentials. The runner scrubs all token and API key environment variables (`GITHUB_TOKEN`, `OPENAI_API_KEY`, etc.) before launching steps.
6. **Transactional Rollback**: When a `write_path: true` procedure fails on a clean git working tree, the harness automatically invokes git rollback to prevent partial workspace corruption.

