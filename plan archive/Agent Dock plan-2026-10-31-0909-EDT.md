# Brain Harness — Agent Dock Plan

**Created:** 2026-10-31 09:09 EDT (Redrafted 2026-10-31 with live-code verification, resolved Track 0 design decisions, and `AGENTS.md` architectural invariants)
**Repo:** `SpectreDeath/brain-harness`
**HEAD at planning time:** `901996e` / `8ba3f55` (main)
**Purpose:** Turn the "Agent Dock" sketch into a buildable, file-and-line-anchored plan while keeping simplicity as its hallmark. Same pattern as the sibling plans: small, checkable items to pick through one at a time, with an explicit deferred list (Track 7) for everything that only gets built if a real limitation demands it.
**The idea, as sketched 2026-10-31:** Inspired by the Muse GitHub App connection, a dock is a place in a repository that lets an agent link to it. Workstation dock, not boat dock: one connection and the agent gains power, monitors, network, peripherals — it plugs in and works from inside the repo. A dock is distinct from a bridge: a bridge translates between two different worlds (the harness's Em-Cubed and Memtext bridges do this); a dock is a port *in* the repository that says "an agent plugs in here." Once docked, the agent clones/links the repo and drives it — uses the repository to do stuff.
**What exists today that the dock builds on (verified against live code 2026-10-31):**
- **Source parsing (`src/harness/ingestion/providers.py:70`):** `parse_repo_source()` already parses `owner/repo` shorthand, GitHub/GitLab/Codeberg/Bitbucket URLs, SSH remotes, and local paths into frozen `ParsedRepoSource` records (`Rule 12`).
- **Why `RepoFetcher` (`src/harness/ingestion/fetcher.py:478, 537-539`) is NOT enough by itself:** `RepoFetcher._fetch_github` downloads ZIP archives without `.git/`, and `_fetch_git_clone` (`fetcher.py:537-539`) explicitly deletes `.git/` (`shutil.rmtree(git_dir)`). A docked agent that needs `git status`, `git diff`, transactional commits, or `git push` requires a real git working tree, so the dock transport layer must preserve `.git/` on clone (into `~/.harness/docks/<owner>__<repo>`) or link directly to an existing local checkout.
- **Workspace & Git primitives (`src/harness/services/filesystem_git.py:108-351`):** `DefaultFilesystemGitService` (`FILESYSTEM_GIT_KEY`) already provides `read_file`, `write_file`, `list_dir`, `search_text`, `git_status`, `git_diff`, `git_log`, `commit_transaction`, and `rollback_transaction` (`Rule 8`), missing only remote `clone` and `push`.
- **Command & boundary security (`plugins/security_and_forensics/codex_execpolicy/`):** `CodexExecPolicyService` (`EXEC_POLICY_KEY`, `evaluate_command_policy` in `evaluator.py:25`) already parses shell commands into recursive AST tokens/subshells (`ast_parser.py`) and enforces catastrophic/destructive command denial (`rules.py:36`, `models.py:68`).
- **Plugin & tool mounting (`src/harness/plugins/sandboxed.py:190-209`, `src/harness/commands/tools.py`):** `SandboxedPlugin` auto-mounts `plugin.json` entrypoints into `ToolRegistry`, and `AGENTS.md` provides repo-side prose guidance. The dock is the repo-level declarative equivalent of `plugin.json`: one declared port for a whole repository instead of one plugin.

## Guiding principles (the plan's constitution — do not drift from these without a recorded reason)

- **Simplicity first.** Build the smallest dock that works. Add nothing — no schema police, no policy engine, no registry service — until a real limitation points at it. Track 7 holds everything deferred; it is not a backlog to burn through, it is a list of things to *not* build yet.
- **Repo declares, harness falls back.** The repo declares its dock in repo-root `dock.yaml`; the harness provides a deterministic generic dock (read, search, status/diff, standard test runner if detected, transactional write, push) for repos that declare none. A declared dock overrides the generic one.
- **Declaration is data, not logic.** The dock manifest is YAML data — tools, entrypoints/procedures, permissions, boundaries — not Prolog-style rules and not executable code. It is parsed strictly with `yaml.safe_load()` (never `yaml.load()`), and nullable YAML keys are normalized via `raw.get("key") or []` / `or {}` (`Rule 33`).
- **YAML because procedures live there.** GitHub Actions, Ansible, CI configs — procedural instructions as data is YAML's home turf. A dock manifest holds both static declarations and sequential procedures, and humans can read it. JSON is valid YAML, so machine tooling can emit JSON and humans can write YAML.
- **Read without running.** Nothing about discovering or inspecting a dock may execute code from the target repository. Manifest loading, procedure listing, and tool inspection are pure file reads + YAML parsing.
- **Dock ≠ bridge ≠ plugin.** A bridge (`src/harness/bridges/`) translates between two external ecosystems. A plugin (`plugins/<category>/<name>/plugin.json`) registers capabilities inside the harness IoC container. A dock (`dock.yaml`) is a repo-level port an agent plugs into to drive that repository from inside.
- **Micro-kernel seam & zero new dependencies (`Rules 1, 2, 6, 49` + repo guardrail).** The dock v0 uses `pyyaml` and `click` (already in `pyproject.toml`), exposes a typed `DockService` protocol and `DOCK_SERVICE_KEY = ServiceKey[DockService]("service.dock")` in `src/harness/services/dock.py`, and registers a single `("dock", dock_group)` entry in `src/harness/cli.py:_CANONICAL_GROUPS` (`Rule 6`).

---

## Track 0 — Design decisions (settled 2026-10-31 against live repo seams)

- [x] **Confirm the repo-declares direction:** Repo declares its dock via `dock.yaml`; when absent, `DockService` synthesizes a `GenericDockManifest` (`declared=False`) with safe default boundaries.
- [x] **Lock the manifest location vs local state location:**
  - **Repo manifest:** Repo-root **`dock.yaml`** is the single supported manifest location. `.harness/dock.yaml` is an explicit non-option because `.gitignore:55` ignores `.harness/*` by default and external repositories are not required to carry a `.harness/` directory.
  - **Local approval & link ledger:** **`.harness/docks.json`** in the active harness workspace stores linked dock records and approved manifest SHA-256 digests (local runtime state, properly ignored by `.gitignore:55`).
- [x] **Define "drive" concretely for v0:**
  - **In v0:** (1) `read` (inspect files, directory tree, `git status`/`git diff`/`git log` via `DefaultFilesystemGitService`), (2) `run` (execute declared sequential procedures inside the repo's working directory), (3) `write` (modify files inside non-boundary paths, wrapped in `DefaultFilesystemGitService` rollback checkpoints per `Rule 8`), and (4) `push` (opt-in `git push` to non-protected branch when `permissions.push: true` is both declared and approved).
  - **Explicitly excluded from "drive":** Force-push (`git push --force`), hard reset (`git reset --hard`), untracked purge (`git clean -fd`), path traversal outside `repo_root`, credential harvesting, and arbitrary shell execution during dock discovery.
- [x] **Define the separation between `dock.yaml`, `plugin.json`, and `AGENTS.md`:**
  - `dock.yaml` (machine-readable repo port): declares runnable repo procedures (`entrypoints`), exposed tool references (`tools`), boolean capability flags (`permissions`), and hard path/command exclusions (`boundaries`).
  - `plugin.json` (harness capability package): declares a single drop-in plugin's IoC service keys, Python module entrypoint, and `ToolRegistry` schemas under `plugins/<category>/<name>/`.
  - `AGENTS.md` (prose architectural rules): human-and-LLM coding standards, architectural invariants (`Rules 1–58`), and design rationale that guide reasoning rather than defining a parser schema.
- [x] **Define the permission & approval model:**
  - **Repo owner** declares maximum intended capabilities and boundaries in `dock.yaml`.
  - **Operator/user** approves a specific declaration at `harness dock link` time (keyed by canonical `sha256` of `dock.yaml`, persisted in `.harness/docks.json`). Any byte change to `dock.yaml` invalidates the stored `approved_sha256` and blocks `dock run` until re-approved (`--approve` / interactive confirmation).
  - **Never allowed (hard-blocked by runner even if declared):** Credential access/env leakage (`Rule 15`), working-directory escape outside `repo_root`, and destructive git/filesystem commands flagged by `CodexExecPolicyService` (`_DEFAULT_DENY_PATTERNS`) or `AGENTS.md` guardrails.
- [x] **Lock the transport layer (`local` first, `git` clone second, one interface above both):**
  - Transport 1 (`local`): Links directly to an existing local git checkout path (zero network; primary path for unit tests and Track 4 self-dogfooding on `D:\GitHub\projects\Brain Harness`).
  - Transport 2 (`git`): Parses remote `owner/repo` or Git URLs via `parse_repo_source` (`src/harness/ingestion/providers.py:70`) and runs `git clone` into `~/.harness/docks/<owner>__<repo>` **without stripping `.git/`** (unlike `RepoFetcher._fetch_git_clone`).
- [x] **Canonical one-paragraph dock definition (for `docs/how-to/agent-dock.md`):**
  > An **Agent Dock** is a repository-level declarative port (`dock.yaml`) that tells an agent how to plug into a repository and drive it from the inside — like a workstation dock that connects power, display, and peripherals through a single port. Unlike a **plugin** (`plugin.json`, which installs a single capability into the harness kernel) or a **bridge** (`src/harness/bridges/`, which translates between two external ecosystems), a dock describes the repository itself as an operable workspace: its runnable procedures, its recommended tools, its permission flags (`read`, `run`, `write`, `push`), and its off-limits boundaries. Discovering a dock parses YAML data without executing repo code; driving a dock requires explicit user approval of the manifest digest and runs every procedure step inside a boundary-enforced, credential-scrubbed subprocess rooted in the repository.

---

## Track 1 — Minimal dock manifest spec & slotted models (v0)

- [x] Create `src/harness/services/dock.py` with slotted/frozen dataclasses (`Rule 12`, `Rule 43`) and a `@runtime_checkable` `DockService` protocol + `DOCK_SERVICE_KEY = ServiceKey[DockService]("service.dock")` (`Rules 2, 49`):
  - `DockPermissions(read: bool = True, run: bool = True, write: bool = False, push: bool = False)` (`slots=True, frozen=True`).
  - `DockBoundaries(paths: tuple[str, ...] = (), operations: tuple[str, ...] = ())` (`slots=True, frozen=True`).
  - `DockStep(command: str = "", workdir: str = ".", expected_output: str = "", call_procedure: str | None = None)` (`slots=True, frozen=True`, with `__post_init__` asserting exactly one of `command` or `call_procedure` is non-empty).
  - `DockProcedure(name: str, description: str = "", steps: tuple[DockStep, ...] = (), write_path: bool = False)` (`slots=True, frozen=True`).
  - `DockManifest(name: str, description: str, declared: bool, manifest_path: str | None, sha256: str, entrypoints: dict[str, DockProcedure], tools: tuple[str, ...], permissions: DockPermissions, boundaries: DockBoundaries, warnings: tuple[str, ...] = ())` (`slots=True, frozen=True`).
- [x] Implement `load_dock_manifest(repo_root: Path) -> DockManifest` (pure read, zero code execution):
  - Look strictly at `repo_root / "dock.yaml"`. If `.harness/dock.yaml` exists without root `dock.yaml`, emit a clear warning in `warnings` noting that only repo-root `dock.yaml` is supported.
  - Parse via `yaml.safe_load()`; apply **Rule 33** null-field fallbacks (`raw.get("entrypoints") or {}`, `raw.get("tools") or []`, `raw.get("permissions") or {}`, `raw.get("boundaries") or {}`).
  - Malformed YAML or non-mapping root raises `DockManifestError(path, reason)` naming `dock.yaml` and the line/problem, never an unhandled parser traceback.
- [x] Loose validation only (simplicity rule): verify required top-level fields (`name`, `description`) and coerce types safely; record unknown top-level or step keys into `DockManifest.warnings` rather than rejecting the file.
- [x] Implement `build_generic_dock_manifest(repo_root: Path) -> DockManifest` (`declared=False`):
  - Auto-detect standard read-only/test entrypoints purely by file existence (`pyproject.toml` / `tests/` → `test: pytest -q`, `status: git status --short`); set default permissions (`read=True, run=True, write=False, push=False`) and default boundaries (`paths=(".git/", ".env", ".pytest_cache/", "src/harness/ui/static/")`, `operations=("git push --force", "git reset --hard", "git clean -fd", "credential_access")`).
- [x] Author the real repo-root `dock.yaml` for `brain-harness` itself (used both as the Track 1 spec reference and the Track 4 dogfood manifest).

---

## Track 2 — Docking service and `harness dock` CLI group

- [x] Implement `DefaultDockService` in `src/harness/services/dock.py` and `resolve_dock_service(context)` (following the `resolve_icm_architect_service` / `Rule 58` adapter seam pattern):
  - State persistence in `.harness/docks.json` (configurable `state_file: Path` for test isolation), storing `DockLinkRecord(dock_name, repo_source, repo_path, transport, declared, manifest_sha256, approved, approved_sha256, linked_at)`.
  - Transport resolution: if `source` is an existing local directory (`Path(source).is_dir()`), use `transport="local"`; otherwise parse via `parse_repo_source(source)` (`src/harness/ingestion/providers.py:70`) and clone into `~/.harness/docks/<owner>__<repo>` preserving `.git/`.
- [x] Create `src/harness/commands/dock.py` with Click group `dock_group` (`@click.group("dock")`) and register `("dock", dock_group)` in `src/harness/cli.py:_CANONICAL_GROUPS` (`Rule 6`, `Rule 23` UTF-8 stream reconfiguration):
  - `harness dock inspect [<repo_or_path>] [--json]`: read-only discovery of a repo's dock (`declared` vs `generic`, permissions, boundaries, procedures, tools, `sha256`, warnings) without linking or writing state.
  - `harness dock link <repo_or_path> [--name ALIAS] [--approve] [--json]`: resolve transport, load manifest (or generic fallback), display declaration summary + boundaries + `sha256`, prompt via `click.confirm("Approve docking with these permissions and boundaries?")` (or accept `--approve` for non-interactive CLI/tests), and persist the `DockLinkRecord` in `.harness/docks.json`.
  - `harness dock list [--json]`: list all linked docks from `.harness/docks.json`, showing `declared` vs `generic`, approval status (`approved` vs `manifest_changed` vs `unapproved` by comparing live `dock.yaml` `sha256` against `approved_sha256`), and repo path.
  - `harness dock tools <dock> [--json]`: list the tools the dock exposes (cross-referenced against live `ToolRegistry` / repo scripts so the user or agent sees which tools are mounted vs repo-local).
  - `harness dock run <dock> <procedure> [--dry-run] [--json]`: verify approval digest match, enforce boundaries on every step (including composed procedures), stream/capture step output, and return structured `DockRunResult`.

---

## Track 3 — Permissions, boundary enforcement, and trust

- [x] **Pre-execution boundary gate (refuse before running, never clean up after):**
  - Before executing any step in `DockService.run`, validate:
    1. **Approval integrity:** `record.approved` is `True` and `live_manifest.sha256 == record.approved_sha256`. If `dock.yaml` was modified after `dock link`, refuse execution with `DockApprovalDriftError` instructing the user to re-run `harness dock link <repo> --approve`.
    2. **Permission gate:** Running any procedure requires `permissions.run == True`; procedures marked `write_path: true` (or touching write operations) require `permissions.write == True`; any `git push` command requires `permissions.push == True`.
    3. **Workdir confinement:** Resolve `(repo_root / step.workdir).resolve()` and assert `.is_relative_to(repo_root.resolve())` so a step cannot escape the repository via `../../`.
    4. **Path & operation boundary gate:** Tokenize the step command (reusing `CodexExecPolicyService` / `_check_danger_patterns` from `plugins/security_and_forensics/codex_execpolicy/engine/rules.py:36` plus manifest `boundaries.paths` and `boundaries.operations`). Any match against a boundary path (e.g., `.git/config`, `.env`, `src/harness/ui/static/`), destructive git operation (`git push --force`, `git reset --hard`, `git clean -fd`), or subshell injection is refused before subprocess spawn, naming the exact boundary violated.
- [x] **Credential exclusion & environment scrubbing (`Rule 15`):**
  - Manifest loader rejects or strips any manifest field attempting to declare credential/secret access, and step validator refuses commands referencing credential stores (`.env`, `.git-credentials`, `printenv`, `env`).
  - Subprocess runner constructs a sanitized environment dict that strips secret/token variables (`GITHUB_TOKEN`, `GH_TOKEN`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `AWS_SECRET_ACCESS_KEY`, `HARNESS_*_TOKEN`) while setting `PYTHONIOENCODING="utf-8"` (`Rule 23`).
- [x] **Subprocess isolation & resource hygiene (`Rules 5, 8, 14, 53`):**
  - Execute each step via `asyncio.create_subprocess_exec` / `subprocess.run` (or platform shell only when pipes/redirection are required and AST-validated), draining `stderr` into a bounded `deque(maxlen=50)` ring buffer (`Rule 53`) and explicitly closing `stdin`/`stdout`/`stderr` pipes inside `finally:` (`Rule 14`).
  - When a `write_path: true` procedure step fails (non-zero exit or timeout) on a git repo, automatically invoke `DefaultFilesystemGitService.rollback_transaction(repo_path)` (`Rule 8`) if the workspace was clean before the procedure started, preventing partial dirty state.
- [x] **Trust paragraph in docs:** Document in one plain-language paragraph who declares (`dock.yaml` author), who approves (operator at `harness dock link`), what is never allowed (credential access, destructive git ops, workdir escape, code execution during discovery), and what happens when `dock.yaml` changes (SHA-256 mismatch blocks execution until re-approved).

---

## Track 4 — Dogfood: dock `brain-harness` itself

- [x] Promote the Track 1 manifest to repo-root `D:\GitHub\projects\Brain Harness\dock.yaml`, declaring:
  - `name: brain-harness`
  - Three real procedures (Track 5): `vault-stats` (read-only knowledge graph stats), `verify-core` (verification test subset), and `sync-context` (write-path context sync/lint check).
  - Genuine `tools` references (`fs_read_file`, `fs_search_text`, `fs_git_status`, `fs_git_diff`, `run_pytest`) and `boundaries` (`.git/`, `.env`, `.pytest_cache/`, `src/harness/ui/static/`, `git push --force`, `git reset --hard`, `git clean -fd`).
- [x] Exercise the full declared-dock loop against `brain-harness`:
  - `harness dock link . --approve`
  - `harness dock list` (verifying `declared=True` and `approved_sha256` match)
  - `harness dock tools brain-harness`
  - `harness dock run brain-harness vault-stats` and `harness dock run brain-harness verify-core`
- [x] Exercise the generic-dock fallback loop against an undeclared temporary git repo (no `dock.yaml`), confirming `harness dock link` reports `declared=False (generic fallback)`, enforces default boundaries, and runs the generic `status` / `test` procedures.
- [x] Fold any friction discovered during dogfooding directly back into `src/harness/services/dock.py` and `src/harness/commands/dock.py` before closing Track 4.

---

## Track 5 — Procedures as YAML, done properly (still simple)

- [x] **Step model v0, locked:** Sequential steps only; each step specifies either `command` (with optional `workdir` defaulting to `"."` and optional `expected_output` note) or `call_procedure` (procedure composition by name). No conditionals, no loops, no Jinja/variable templating in v0.
- [x] **Step execution & failure semantics:** Stream/capture `stdout` and `stderr`, check `returncode == 0`, halt immediately on the first non-zero exit code (no silent continuation), and report `failed_step_index`, `failed_step_command`, `returncode`, and trailing `stderr` (`Rule 53`) in `DockRunResult`.
- [x] **Bounded procedure composition (cycle-safe):** Allow a step with `call_procedure: <other_procedure>` to inline-execute another procedure declared in the same `dock.yaml`. Track visited procedure names in a call stack (`max_depth=5`) so direct or mutual recursion (`A -> B -> A`) raises a clear `DockProcedureCycleError` before execution.
- [x] **Three real procedures in `brain-harness`'s `dock.yaml`:**
  1. `vault-stats` (read-only): `python src/harness/cli.py knowledge stats`
  2. `verify-core` (verification): `pytest tests/test_service_dock.py tests/test_command_dock.py -v`
  3. `sync-context` (write-path, `write_path: true`): `python src/harness/cli.py context lint --root .`

---

## Track 6 — Docs and light gates

- [x] Write `docs/how-to/agent-dock.md` (strictly relative links per `Rule 47`, zero `file:///` URIs):
  - Workstation dock metaphor and the `dock ≠ bridge ≠ plugin` distinction table.
  - The v0 `dock.yaml` schema with `brain-harness`'s own `dock.yaml` as the worked example.
  - CLI walkthrough (`harness dock inspect`, `link`, `list`, `tools`, `run`).
  - The Track 3 trust & approval-digest paragraph and the generic dock fallback specification.
- [x] Update `docs/reference/cli.md` with the `harness dock` command group (`inspect`, `link`, `list`, `tools`, `run`) so CLI reference docs stay synchronized with `_CANONICAL_GROUPS`.
- [x] Add light drift & contract test suite `tests/test_service_dock.py` and `tests/test_command_dock.py`:
  - Asserts repo-root `dock.yaml` parses cleanly with zero warnings, its declared procedures execute/dry-run cleanly, generic fallback works on an undeclared repo, `dock.yaml` mutation triggers `DockApprovalDriftError` until re-approved, boundary violations and workdir escapes (`../`) are refused before execution, env secrets are scrubbed (`Rule 15`), and `docs/how-to/agent-dock.md` contains zero `file:///` links (`Rule 47`).

---

## Track 7 — Deferred: only if a real limitation demands it (do NOT build these preemptively)

- [ ] Strict JSONSchema/Pydantic rejection of unknown manifest keys (build when malformed docks cause a real failure that loose validation misses, not before).
- [ ] Policy engine / Datalog-style rule evaluation for permissions (build when boolean `read`/`run`/`write`/`push` flags + path/operation boundaries prove insufficient for a real dock, not before).
- [ ] Central dock registry or remote discovery index (build when there are enough docks that finding them is a real problem, not before).
- [ ] Multi-harness dock spec / cross-harness portability conformance suite (build when a second harness wants to dock, not before).
- [ ] MCP server exposure of docked procedures/tools (build when an outside agent needs dock access over MCP rather than CLI/`DockService`, not before).
- [ ] Conditional, loop, or matrix procedure steps (build when a real procedure cannot be expressed sequentially or via `call_procedure` composition, not before).
- [ ] Dock manifest schema versioning and automated migration (build when a v1 format change breaks a real v0 dock, not before).

---

## Suggested order (the pick queue)

1. **Track 0 (design decisions)** — settled above against live codebase seams (`providers.py`, `filesystem_git.py`, `codex_execpolicy`, `.gitignore`).
2. **Track 1 (minimal manifest spec & slotted models)** — `src/harness/services/dock.py` models, `yaml.safe_load` loader (`Rule 33`), generic dock builder, and repo-root `dock.yaml`.
3. **Tracks 2 + 3 together (docking service, CLI group, and boundary/approval enforcement)** — `DefaultDockService`, `harness dock` commands (`inspect`, `link`, `list`, `tools`, `run`), SHA-256 approval ledger in `.harness/docks.json`, pre-execution boundary/AST checks, and env secret scrubbing.
4. **Track 5 (procedure runner & composition)** — sequential runner, cycle-safe `call_procedure`, `Rule 8` write rollback, and `Rule 14/53` pipe/stderr disposal.
5. **Track 4 (dogfood `brain-harness` itself)** — run the live CLI against `brain-harness`'s `dock.yaml` and a generic fallback fixture repo; fold fixes back immediately.
6. **Track 6 (docs and light gates)** — `docs/how-to/agent-dock.md`, `docs/reference/cli.md`, and `tests/test_service_dock.py` + `tests/test_command_dock.py`.
7. **Track 7 (deferred)** — only on evidence of a real limitation. This track succeeds by staying empty in v0.

---

## §11 Verification backlog (resolved during 2026-10-31 review)

- [x] ~~Verify: whether the GitHub App transport or the local-clone transport is the better first dogfood path.~~ **Verified 2026-10-31:** Inside `src/harness/`, there is no dedicated GitHub App connector (`RepoFetcher` in `src/harness/ingestion/fetcher.py:478, 537-539` fetches ZIPs or clones and deletes `.git/`). Local checkout transport (`transport="local"`) is the right first dogfood path (offline, zero network, preserves `.git/` for `DefaultFilesystemGitService`), while remote `owner/repo` / Git URLs use `parse_repo_source` (`src/harness/ingestion/providers.py:70`) + `git clone` into `~/.harness/docks/<owner>__<repo>` with `.git/` preserved.
- [x] ~~Verify: manifest location conventions — repo-root `dock.yaml` vs `.harness/dock.yaml` — against how the repo already treats root-level vs `.harness/` files.~~ **Verified 2026-10-31:** `.gitignore:55-58` ignores `.harness/*` by default because `.harness/` holds local runtime state (`events.jsonl`, `storage.db`). Therefore, the repository's declared manifest belongs at repo-root **`dock.yaml`**, while local link/approval state belongs in **`.harness/docks.json`**.
- [x] ~~Verify: whether any existing concept in the repo already covers part of the dock closely enough that the dock should reuse it rather than add a new file.~~ **Verified 2026-10-31:** No existing manifest covers repo-level docking (`plugin.json` is per-plugin IoC/tool packaging; `SKILL.md`/`CARD.md` is procedural prompt guidance), so `dock.yaml` is warranted. However, four internal seams should be reused directly by `DockService`: `parse_repo_source` (`src/harness/ingestion/providers.py:70`), `DefaultFilesystemGitService` (`src/harness/services/filesystem_git.py:183`), `CodexExecPolicyService` / `_check_danger_patterns` (`plugins/security_and_forensics/codex_execpolicy/engine/rules.py:36`), and `.harness/` state persistence.
- [x] ~~Verify: the exact approval UX for `harness dock link` against the runtime's approval-card patterns.~~ **Verified 2026-10-31:** CLI commands use `click.confirm()` after printing the declaration summary and `sha256` digest (with `--approve` for non-interactive/test runs and automatic refusal on non-TTY stdin without `--approve`), persisting `approved_sha256` in `.harness/docks.json` and blocking `harness dock run` whenever the live `dock.yaml` digest diverges from `approved_sha256`.
