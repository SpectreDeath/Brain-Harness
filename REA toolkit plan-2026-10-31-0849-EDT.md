# Brain Harness — REA Toolkit Plan

**Created:** 2026-10-31 08:49 EDT (Redrafted 2026-10-31 with live-code verification, resolved Track 0 & §11 decisions, sibling service integration, and `AGENTS.md` architectural invariants)
**Repo:** `SpectreDeath/brain-harness`
**HEAD at planning time:** `fe76eb0` / `901996e` (main)
**Purpose:** Turn the REA reverse-engineering ecosystem from disconnected plugins and verification primitives into one unified, easy-to-access toolkit (`harness rea`, `service.rea_toolkit`, `rea.*` aliases, and `rea-reverse-engineering` skill) — and close the endogenous loop the harness is built for: a harness that dissects an artifact, seals canonical evidence (`ev:<sha256>`), and distills semantic signatures into the Knowledge Vault with Isnad lineage.

---

## Baseline (measured & code-verified 2026-10-31 against local clone)

### 1. The Four Dissection Plugins (28 tools total)

All four dissection plugins have both a `plugin.json` manifest (`"isolation": "subprocess"`, `"trusted": true`) and a deepened Python engine + `HarnessPlugin` singleton (`Rule 45`, `Rule 49`):

- **`plugin.rea_javascript`** (`plugins/data_engineering/rea_javascript/main.py`, `src/harness/services/rea_javascript.py`, `REA_JAVASCRIPT_KEY = ServiceKey("service.rea_javascript")`, 5 tools):
  - `rea_javascript_recover_sources` (Wakaru `^1.13.0` bundle deobfuscation)
  - `rea_javascript_electron_inspect` (Electron ASAR manifest, preload, and IPC channels)
  - `rea_javascript_web_observe` (passive CDP DOM/script/network observation)
  - `rea_javascript_dotnet_inspect` (.NET PE/CLI type hierarchies, CIL body hashes, P/Invoke)
  - `rea_javascript_har_inspect` (offline HAR 1.2 / mitmproxy capture analysis)
- **`plugin.rea_managed_runtime`** (`plugins/security_and_forensics/rea_managed_runtime/main.py`, `src/harness/services/rea_managed_runtime.py`, `REA_MANAGED_RUNTIME_KEY = ServiceKey("service.rea_managed_runtime")`, 5 tools):
  - `rea_inspect_managed_artifact` (Windows PE/CLI headers, CLR metadata streams, assembly members)
  - `rea_inspect_managed_native_boundaries` (`ModuleRef`, `ImplMap`, and P/Invoke native boundaries)
  - `rea_inspect_il2cpp_metadata` (Unity IL2CPP `global-metadata.dat` versions 24, 27, 29, 31, 39)
  - `rea_inspect_model_artifact` (zero-allocation byte-seek GGUF v2/v3 and `.safetensors` header inspection; `Rule 48`)
  - `rea_inspect_python_pyc` (CPython 3.7–3.13 `.pyc` header and opcode disassembly)
- **`plugin.rea_mobile_firmware`** (`plugins/security_and_forensics/rea_mobile_firmware/main.py`, `src/harness/services/rea_mobile_firmware.py`, `REA_MOBILE_FIRMWARE_KEY = ServiceKey("service.rea_mobile_firmware")`, 11 tools):
  - `rea_mobile_apk_inspect`, `rea_mobile_jadx_decompile`, `rea_mobile_android_search_classes`, `rea_mobile_android_trace_references`
  - `rea_mobile_adb_inspect_client`, `rea_mobile_adb_list_devices`, `rea_mobile_adb_list_packages`, `rea_mobile_adb_pull_package`, `rea_mobile_adb_read_logcat`
  - `rea_firmware_regions_inspect` (Binwalk 3.1.0), `rea_firmware_extract` (Unblob 26.6.4)
- **`plugin.rea_native`** (`plugins/security_and_forensics/rea_native/main.py`, `src/harness/services/rea_native.py`, `REA_NATIVE_KEY = ServiceKey("service.rea_native")`, 7 tools):
  - `rea_native_batch_decompile` (Ghidra / Hopper / IDA headless batch decompilation)
  - `rea_native_call_graph` (caller/callee traversal)
  - `rea_native_elf_layout` (ELF/PE sections, imports/exports, checksec mitigations)
  - `rea_native_wasm_inspect` (WABT 1.0.42 sections, imports/exports, WAT disassembly)
  - `rea_native_evm_interface` (EVM 4-byte dispatch selectors, opcode count, ABI resolution)
  - `rea_native_annotate_function` (atomic session DB annotation)
  - `rea_native_inspect_load_image` (DOS MZ / COM load image verification against target snapshot)

### 2. Already-Landed REA Epistemic & Forensic Siblings (Reuse — Do Not Reinvent per `Rule 20`)

Earlier planning noted `ki-rea-facet-availability-semantics` and `ki-rea-reconstruction-obligations` in the vault, but live-code inspection confirms their runtime services, CLI groups, and skills **already exist** in the codebase:

- **Differential Facet Verifier (`src/harness/services/differential_facet.py`, `src/harness/commands/facet.py`, `.agents/skills/differential-facet-verifier/`):**
  - Already defines slotted/frozen dataclasses (`Rule 12`, `Rule 43`): `FacetAvailability(available: bool, reason: str | None = None)` (`L70-L80`), `CoverageDeclaration(scope, status, truncated, omitted_count)` with `.absence_claimable` property (`L86-L107`), `DimensionOutcome` (`L109-L139`), and `DifferentialReport` (`L141-L163`, `rep:<sha256>`).
  - Already exposes `DIFFERENTIAL_FACET_SERVICE_KEY = ServiceKey("service.differential_facet")`, `StandardDifferentialFacetService.compare_observations()`, and `harness facet compare|claim-absence|verify|export` (alias `differential-facet` in `src/harness/commands/aliases.py:81`).
- **Reconstruction Obligation Ledger (`src/harness/services/reconstruction_obligation.py`, `src/harness/commands/rol.py`, `.agents/skills/reconstruction-obligation-ledger/`):**
  - Already defines `CanonicalEvidence` (`ev:<sha256>`, `L79-L94`), `ObligationItem` across the 10 REA layers (`cli`, `protocol`, `electron`, `persistence`, `process`, `runtime`, `packaging`, `native-abi`, `application`, `other`) and 8-state FSM (`L96-L116`), and `ReconstructionProof` (`L118-L128`).
  - Already exposes `RECONSTRUCTION_OBLIGATION_SERVICE_KEY = ServiceKey("service.reconstruction_obligation")`, `StandardReconstructionObligationService.ingest_evidence()`, and `harness rol ingest|obligation|verify|export` (alias `obligation-ledger` in `src/harness/commands/aliases.py:80`).
- **Magika Content & Format Forensics (`plugins/security_and_forensics/magika_content_detector/main.py`, `plugins/security_and_forensics/magika_format_forensics/main.py`):**
  - Already provides `MAGIKA_CONTENT_DETECTOR_KEY` (`identify_path`, magic-header fallback) and `MAGIKA_FORMAT_FORENSICS_KEY` (`audit_extension_mismatch`, `polyglot_check`).

### 3. Critical Architectural Seam Catch (Resolved from §11 Verification Backlog)

- **How manifest-mounted REA plugins execute at runtime (`src/harness/plugins/loader.py:329-349`, `src/harness/plugins/sandboxed.py:175-212`):**
  - Because each REA `plugin.json` declares `"isolation": "subprocess"`, `PluginLoader._load_manifest_plugin` returns a `SandboxedPlugin` (`ManifestPlugin`) wrapper rather than importing `main.py` in-process (`Rule 5`, `Rule 7`).
  - During `SandboxedPlugin.on_load(ctx)` (`sandboxed.py:180-181`), `SandboxedPlugin` registers **`self`** under `ServiceKey("service.rea_native")` (etc.).
  - **The Trap:** `SandboxedPlugin` exposes `.invoke_typed(method, params)` and `.call(method, params)` (which dispatch JSON-RPC over stdio to `bridge_runner.py` invoking top-level functions like `rea_native_elf_layout` in `main.py`), **not** the Python protocol methods (`.elf_layout()`, `.batch_decompile()`) on `ReaNativeService`!
  - **The Fix (`Rule 58` Adapter Invariant):** `resolve_rea_toolkit(ctx)` (and the underlying per-domain resolvers) must detect whether the IoC-registered provider is a `SandboxedPlugin` (dispatching via `.invoke_typed()` / lazy engine adapter), an in-process `Rea*Service` / `Rea*Plugin` instance, or a `MagicMock(spec=...)` test double, adapting all three transparently behind one synchronous/asynchronous facade seam.

### 4. What Does NOT Exist Today (The Exact Scope of This Plan)

1. **No `src/harness/services/rea_toolkit.py` (`service.rea_toolkit`)** unifying artifact routing, envelope normalization, provider binary detection, and signature extraction across the 4 dissection plugins + `DifferentialFacetService` + `ReconstructionObligationService`.
2. **No `harness rea` CLI group (`src/harness/commands/rea.py`)** providing a single human/headless entrypoint (`inspect`, `list`, `decompile`, `callgraph`, `signatures`, `devices`, `diff`, `learn`, `providers`).
3. **No `rea.*` canonical tool alias table** in `ToolRegistry` (`src/harness/services/tools/registry.py`) to normalize the inconsistent entrypoint prefixes (`rea_javascript_*` vs `rea_inspect_*` vs `rea_mobile_*` vs `rea_firmware_*` vs `rea_native_*`) without breaking existing tool names or duplicating LLM tool schemas.
4. **No `.agents/skills/rea-reverse-engineering/` upstream triage skill** routing artifact dissection into `../differential-facet-verifier/SKILL.md` and `../reconstruction-obligation-ledger/SKILL.md`.
5. **No live `rea diff` or `rea learn` bridge** connecting live binary dissection outputs directly to `DifferentialFacetService.compare_observations()` (`rep:<sha256>`), `ReconstructionObligationService.ingest_evidence()` (`ev:<sha256>`), and Knowledge Vault dual-file items (`.harness/knowledge/<ki_id>/metadata.json` + `summary.md`).

---

## Guiding Decisions (Settled & Locked in Track 0)

- **Facade & composition, not rewrite (`Rule 20`, `Rule 49`).** The facade routes, normalizes, and composes; the four REA plugins perform dissection, `DifferentialFacetService` computes 3-valued diffs, and `ReconstructionObligationService` mints `ev:<sha256>` canonical evidence records.
- **Unify `FacetAvailability`, don't fork a third copy (`Rule 12`, `Rule 20`).** Reuse `FacetAvailability` and `CoverageDeclaration` from `src/harness/services/differential_facet.py` (and align `src/harness/services/reconstruction_obligation.py` to import the same class so `isinstance` checks never split). At the facade presentation layer, every facet maps cleanly to a 3-state status (`"available"`, `"absent"`, `"unknown"`) backed by `FacetAvailability(available: bool, reason: str | None)` and `CoverageDeclaration.absence_claimable`:
  - `"available"`: `FacetAvailability(available=True)` with non-empty observations.
  - `"absent"`: `FacetAvailability(available=True)` with zero items **AND** `coverage.absence_claimable == True` (`status == "complete" and not truncated and omitted_count == 0`).
  - `"unknown"`: `FacetAvailability(available=False, reason=...)` **OR** an empty facet where `coverage.absence_claimable == False` (e.g., missing external binary, truncated budget, unsupported OS such as Binwalk/Unblob on Windows).
- **One canonical result envelope (`DissectionEnvelope`).** All facade operations emit a single structured envelope containing:
  1. `artifact`: `ArtifactIdentity(path, sha256, size_bytes, detected_kind, mime_type, magic_summary, polyglot_warnings)`
  2. `facets`: `dict[str, FacetEnvelope]` (each carrying `state: Literal["available", "absent", "unknown"]`, `availability: FacetAvailability`, `coverage: CoverageDeclaration`, and `data: Any`)
  3. `signatures`: `list[SemanticSignature]` (normalized selectors, IPC channels, P/Invoke declarations, imported/exported symbols, class/method refs, URLs/endpoints)
  4. `provider`: `ProviderProvenance(plugin, tool, binary_name, binary_path, binary_version, execution_mode)`
  5. `evidence_id`: deterministic `ev:<sha256>` computed via `canonicalize_json` (`src/harness/services/differential_facet.py:56`)
- **Offline and non-executing by default.** Dissection never executes the target binary, never imports target `.pyc`/`.dll` in-process, never contacts recorded HAR hosts, and never phones home.
- **Learned signatures are first-class Vault & Ledger citizens (`Rule 40`, `Rule 41`).** `harness rea learn` writes through the canonical vault persistence path (`SQLiteStorageService` + dual-file `.harness/knowledge/<ki_id>/metadata.json` + `summary.md` + `backfill_edges_mechanically` / `propose_links`), anchored by an Isnad chain referencing the artifact's `ev:<sha256>` evidence record.

---

## Track 0 — Foundations & Settled Design Decisions

- [ ] **Deterministic Artifact-Type Routing Table (`src/harness/services/rea_toolkit.py`):**
  Inspect magic bytes first (first 512 bytes + container central directory/headers), then file extension/name, optionally enriched by `MAGIKA_CONTENT_DETECTOR_KEY` / `MAGIKA_FORMAT_FORENSICS_KEY` when loaded. Overlaps are settled explicitly:
  1. **ELF binary** (magic `\x7fELF`): route to `plugin.rea_native` → `rea_native_elf_layout` (primary structural + checksec) and `rea_native_batch_decompile` / `rea_native_call_graph` (when symbols requested or decompiler available).
  2. **Windows PE / .NET CLI vs Native PE** (magic `MZ` + `PE\0\0` at `e_lfanew`):
     - Inspect the PE Optional Header Data Directory #14 (`IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR` / CLR Runtime Header RVA & size):
     - **If CLR Header RVA > 0 (Managed .NET Assembly):** route primary structural & boundary inspection to `plugin.rea_managed_runtime` (`rea_inspect_managed_artifact` + `rea_inspect_managed_native_boundaries`), and enrich with `plugin.rea_javascript` (`rea_javascript_dotnet_inspect`) for `type_hierarchy` and `cil_hashes` facets.
     - **If CLR Header RVA == 0 (Native PE32/PE32+):** route to `plugin.rea_native` (`rea_native_elf_layout` + `rea_native_batch_decompile`).
  3. **DOS MZ / COM Legacy Load Image** (magic `MZ` without `PE\0\0` signature, or `.com` / `.exe` 16-bit header): route to `plugin.rea_native` → `rea_native_inspect_load_image`.
  4. **Android APK** (`PK\x03\x04` ZIP archive containing `AndroidManifest.xml` or `classes.dex`, or `.apk` extension): route to `plugin.rea_mobile_firmware` → `rea_mobile_apk_inspect` (primary) + `rea_mobile_jadx_decompile` (when JADX provider available or `--decompile` requested).
  5. **Electron ASAR Archive** (4-byte pickle header + JSON size prefix, or `.asar` extension): route to `plugin.rea_javascript` → `rea_javascript_electron_inspect`.
  6. **WebAssembly Binary** (magic `\x00asm\x01\x00\x00\x00` or `.wasm`): route to `plugin.rea_native` → `rea_native_wasm_inspect`.
  7. **Unity IL2CPP Metadata** (magic `0xFAB11BAF` at offset 0 or filename `global-metadata.dat`): route to `plugin.rea_managed_runtime` → `rea_inspect_il2cpp_metadata`.
  8. **AI Model Weights** (magic `GGUF` at offset 0 for `.gguf`, or `.safetensors` 8-byte little-endian header size + JSON header): route to `plugin.rea_managed_runtime` → `rea_inspect_model_artifact` (`Rule 48` O(1) byte seeks).
  9. **CPython Bytecode** (`.pyc` extension + valid CPython 3.7–3.13 magic tag `\x0d\x0a`): route to `plugin.rea_managed_runtime` → `rea_inspect_python_pyc`.
  10. **HTTP Archive (HAR 1.2)** (JSON root with `{"log": {"version": ...}}` or `.har` extension): route to `plugin.rea_javascript` → `rea_javascript_har_inspect`.
  11. **JavaScript Bundle** (`.js`, `.mjs`, `.cjs`, or minified bundle heuristics): route to `plugin.rea_javascript` → `rea_javascript_recover_sources`.
  12. **EVM Bytecode** (`0x`-prefixed hex string or `.evm` / `.bin` hex file): route to `plugin.rea_native` → `rea_native_evm_interface`.
  13. **Firmware Image / Blob** (`.bin`, `.fw`, `.img`, SquashFS `hsqs`, CramFS, uImage magic): route to `plugin.rea_mobile_firmware` → `rea_firmware_regions_inspect` (with clean `unknown` facet on non-Linux hosts where Binwalk/Unblob are Linux-gated).
- [ ] **Shared Facet Availability & Envelope Models (`src/harness/services/rea_toolkit.py`):**
  - Re-export `FacetAvailability`, `CoverageDeclaration`, `DimensionOutcome`, `DifferentialReport`, `canonicalize_json`, and `compute_canonical_hash` from `harness.services.differential_facet` (and update `harness.services.reconstruction_obligation` to share `FacetAvailability`).
  - Define `@dataclass(slots=True, frozen=True)` models (`Rule 12`, `Rule 43`) with `.to_dict()` and dict-access compatibility (`__getitem__`, `get`, `__contains__`): `ArtifactIdentity`, `ProviderProvenance`, `SemanticSignature`, `FacetEnvelope`, and `DissectionEnvelope`.
- [ ] **Facade Placement & Dual-Mode Adapter Seam (`Rule 49`, `Rule 58`):**
  - Implement `ReaToolkitService` protocol and `REA_TOOLKIT_KEY = ServiceKey[ReaToolkitService]("service.rea_toolkit")` in `src/harness/services/rea_toolkit.py`, with `resolve_rea_toolkit(ctx: ServiceContext | None = None) -> ReaToolkitService`.
  - Implement `ReaDomainAdapter` inside `src/harness/services/rea_toolkit.py` so that whether a domain plugin (`service.rea_native`, etc.) is registered in `ServiceContext` as a `SandboxedPlugin` (subprocess JSON-RPC), an in-process `HarnessPlugin` / engine, or a `MagicMock` in tests, `ReaToolkitService` invokes it cleanly without `AttributeError`.

---

## Track 1 — `harness rea` CLI Group (`Rule 6`, `Rule 10`, `Rule 23`)

Create `src/harness/commands/rea.py` with a single `@click.group("rea")` definition (`rea_group`), register `("rea", rea_group)` in `src/harness/cli.py:_CANONICAL_GROUPS`, and add `"reverse-engineer": "rea"` and `"dissect": "rea"` to `CLI_ALIASES` in `src/harness/commands/aliases.py`:

- [ ] `harness rea inspect <artifact> [--artifact-type TYPE] [--json]`: auto-detect artifact kind via Track 0 table (or honor `--artifact-type` override), run primary + secondary facet dissections, print the unified `DissectionEnvelope` (artifact hashes, per-facet availability badges `[AVAILABLE]` / `[ABSENT]` / `[UNKNOWN: <reason>]`, extracted signatures, and `ev:<sha256>`), and exit non-zero on undetectable artifact kinds with a diagnostic listing what headers/ detectors were tried.
- [ ] `harness rea list [--artifact-type TYPE] [--json]`: list all 28 REA tools grouped by **artifact kind** (ELF, PE/.NET, APK/Android, JS/Electron/HAR, WASM, EVM, AI Models, Python `.pyc`, Firmware, DOS MZ), showing both the canonical `rea.*` alias and the underlying `plugin.rea_*` tool name plus provider availability.
- [ ] `harness rea providers [--json]`: probe external binary availability (`ghidra` / `analyzeHeadless`, `hopper`, `ida64` / `idat64`, `jadx`, `adb`, `wasm2wat` / WABT, `wakaru`, `binwalk`, `unblob`), reporting installed status, resolved path, version string, and platform support (`linux-only` note on Windows for `binwalk`/`unblob`).
- [ ] `harness rea decompile <artifact> --symbols SYM1,SYM2 [--provider ghidra|hopper|ida] [--json]`: thin wrapper over `rea_native_batch_decompile` emitting a `DissectionEnvelope` where a missing decompiler binary produces `state="unknown"` with `reason="provider '<name>' not installed"`, never an unhandled crash.
- [ ] `harness rea callgraph <artifact> --entry SYMBOL [--depth N] [--direction callee|caller] [--json]`: wrapper over `rea_native_call_graph` in envelope format.
- [ ] `harness rea signatures <artifact> [--kind KIND] [--json]`: extract only the normalized `SemanticSignature` layer (4-byte EVM selectors, Electron IPC channels, P/Invoke `ImplMap` entries, ELF/PE/WASM imports & exports, Android classes/permissions, HAR endpoints) — the exact feed consumed by `harness rea learn`.
- [ ] `harness rea devices [--packages DEVICE_SERIAL] [--json]`: ADB surface (`rea_mobile_adb_inspect_client`, `rea_mobile_adb_list_devices`, `rea_mobile_adb_list_packages`) with missing `adb` or zero attached devices returning explicit `unknown`/`absent` facet envelopes instead of tracebacks.

---

## Track 2 — Unified Facade Service (`src/harness/services/rea_toolkit.py`)

- [ ] **`StandardReaToolkitService` implementation:**
  - `detect_artifact(path_or_hex: str | Path) -> ArtifactIdentity`: pure-Python header/magic inspection + optional `MagikaContentDetectorService` / `MagikaFormatForensicsService` polyglot & extension-mismatch check.
  - `dissect(target: str | Path, *, artifact_type: str | None = None, symbols: list[str] | None = None, provider: str = "ghidra", budgets: ReaDissectionBudgets | None = None) -> DissectionEnvelope`: dispatches via the Track 0 routing table, normalizes tool outputs into `FacetEnvelope` entries with `FacetAvailability` and `CoverageDeclaration`, extracts `SemanticSignature` items, and computes `ev:<sha256>`.
  - `signatures(target: str | Path, *, kind: str | None = None) -> list[SemanticSignature]`: extracts and deduplicates semantic signatures from a `DissectionEnvelope`.
  - `providers() -> dict[str, ProviderProvenance]`: inspects environment paths and engine properties (`ghidra_headless_path`, `wabt_wasm2wat_path`, `jadx_path`, `adb_path`, `shutil.which`) without executing target binaries.
- [ ] **Zero-Fork Budget Enforcement (`Rule 44`):**
  - Load operational bounds from each plugin's `config.default.yaml` (`timeout_seconds`, `max_symbols`, `max_records`, `preview_tensors`, `max_lines`) into `ReaDissectionBudgets(max_symbols=50, max_records=100, max_bytes=10_485_760, timeout_seconds=60.0)`.
  - Whenever a budget truncates output (e.g., symbol count > `max_symbols` or IL2CPP records > `max_records`), set `CoverageDeclaration(scope="dossier", status="partial", truncated=True, omitted_count=omitted)` so `coverage.absence_claimable` evaluates to `False` and any empty observation is quarantined from being claimed `"absent"`.
- [ ] **Provider-Missing Contract:**
  - When an external binary (`analyzeHeadless`, `jadx`, `adb`, `binwalk`, `unblob`, `wasm2wat`) is absent or unsupported on the host OS, the facade still runs pure-Python static facets (ELF/PE layout, APK manifest/DEX parsing, WASM header parsing) and marks only the external-binary facet as `state="unknown"` with `FacetAvailability(available=False, reason="...")`.

---

## Track 3 — `rea-reverse-engineering` Skill (`Rule 37`, `Rule 44`, `Rule 47`, `Rule 55`)

Create `.agents/skills/rea-reverse-engineering/SKILL.md` and `.agents/skills/rea-reverse-engineering/CARD.md` as the upstream triage and dissection skill that connects to the existing REA epistemic skills:

- [ ] **Frontmatter & Catalog Compliance (`Rule 44`):**
  - `description` strictly between 100 and 350 characters, starting with action verbs and ending with an explicit negative boundary (`"Dissect, route, and extract semantic signatures from native binaries, PE/.NET assemblies, Android APKs, JS bundles, WASM, EVM bytecode, and firmware using the unified REA toolkit. Do not use for live exploit execution, network active scanning, or generic source-code linting."`).
- [ ] **`CARD.md` & `SKILL.md` Structural Compliance (`Rule 37`, `Rule 47`):**
  - `CARD.md` uses standard single-pipe ASCII box borders (`┌─...─┐`, `│`, `└─...─┘` — never `║`), includes the exact header tag `SKILL: rea-reverse-engineering`, and provides a `## Mandatory Invariants Checklist` with `- [ ]` items.
  - `SKILL.md` includes the Track 0 artifact routing matrix (including the PE/CLI CLR-header disambiguation rule), the 3-valued facet availability and absence-claimability gate rules, operational budget rules, and an exact `## Anti-Patterns` section with `- **Name** — Description` items.
  - Cross-link using **relative paths** (`Rule 47`): `../differential-facet-verifier/SKILL.md` (for Stage 4 multi-provider comparison) and `../reconstruction-obligation-ledger/SKILL.md` (for Stage 5 `ev:<sha256>` ingestion and obligation closure).
- [ ] **Skill Graph Registration (`Rule 35`, `Rule 55`):**
  - Index the skill via `BuiltinSkillRegistryService` / `index_skill_catalog()` and verify directed edges (`rea-reverse-engineering` → `differential-facet-verifier` → `reconstruction-obligation-ledger`) so `route_intent()` surfaces the full triad without synthetic edge fallback.

---

## Track 4 — Endogenous Learn Loop (`harness rea learn` & `harness rea learned`)

Bridge REA dissection directly into the Knowledge Vault and Reconstruction Obligation Ledger (`Rule 40`, `Rule 41`):

- [ ] **`harness rea learn <artifact> [--dry-run] [--vault .harness/knowledge] [--ledger .harness/reconstruction_ledger.json] [--json]`:**
  1. Dissect `<artifact>` via `ReaToolkitService.dissect()` to obtain the `DissectionEnvelope` and `SemanticSignature` list.
  2. If `--dry-run` is passed, print the candidate Knowledge Item (`ki_id`, title, tags, signature table, Isnad lineage, and candidate `propose_links` edges) without writing to disk.
  3. Otherwise, record the `CanonicalEvidence` (`ev:<sha256>`) via `ReconstructionObligationService.ingest_evidence()` and distill a canonical dual-file Knowledge Item under `.harness/knowledge/<ki_id>/` (`metadata.json` + `summary.md` per `Rule 40`).
  4. Sync into `SQLiteStorageService` and invoke `backfill_edges_mechanically` / `propose_links` (`src/harness/services/storage/vault_operations.py`) so the learned item receives typed graph edges (`derived_from`, `implements`, `related_to`).
- [ ] **Signature-Node Schema & Deterministic Deduplication:**
  - Key learned Knowledge Items deterministically as `ki-rea-sig-<artifact_stem_slug>-<signature_cluster_hash[:8]>`.
  - **What becomes part of the vault item:** normalized semantic signatures (EVM 4-byte selectors + resolved ABIs, Electron IPC channels, P/Invoke `ModuleRef`/`ImplMap` boundaries, exported API surface, Android permissions & entrypoint classes) and facet availability summary.
  - **What is strictly excluded (Trust Boundary):** raw binary blobs, full decompiled pseudocode dumps, and any secret/credential strings encountered in HARs or bundles.
  - **Idempotent Re-Dissection:** Re-running `harness rea learn` on the same artifact + signature digest updates the existing `metadata.json` timestamp and appends provider provenance to the `IsnadChain` (`status="VERIFIED"`, `source_type="rea_dissection"`, `artifact_sha256`, `evidence_id="ev:..."`) rather than creating duplicate vault directories.
- [ ] **Audit & Retrieval Commands (`harness rea learned`):**
  - Add `harness rea learned [--query TEXT] [--vault .harness/knowledge] [--json]` (and tag all REA-distilled items with `"rea-learned"` and `"reverse-engineering"` so `harness knowledge list --tag rea-learned` and `harness knowledge query <domain>` retrieve them immediately).
  - Verify that `export_knowledge_graph()` (`src/harness/services/storage/vault_exporters.py`) includes learned REA nodes and their edges in JSON/GEXF/Cypher exports.

---

## Track 5 — Live Multi-Provider Differential Comparison (`harness rea diff`)

Connect live REA multi-provider dissection to the existing `DifferentialFacetService` (`src/harness/services/differential_facet.py`):

- [ ] **`harness rea diff <artifact> [--providers ghidra,hopper|ida] [--left-file JSON --right-file JSON] [--json]`:**
  - Run `ReaToolkitService.dissect()` across the two requested providers (or compare two saved `DissectionEnvelope` JSON files), project each side into the canonical dossier format expected by `StandardDifferentialFacetService.compare_observations(left, right, providers_differ=True)`, and return a unified report containing both `DissectionEnvelope` summaries and the `DifferentialReport` (`rep:<sha256>`).
- [ ] **Cross-Provider Normalization Rules (Recorded & Enforced):**
  - Map `DissectionEnvelope` facets onto `VALID_DIMENSIONS` (`identity`, `pseudocode`, `assembly`, `comments`, `calls`, `references`, `strings_names`, `cfg` in `differential_facet.py:22-31`).
  - Normalize symbol names (strip leading underscores / provider-generated `sub_` vs `FUN_` address prefixes when comparing by address), sort call-graph edges canonically, and decouple raw disassembly formatting via `providers_differ=True` (`differential_facet.py:373-376`).
  - If either provider is missing or a facet is unavailable on either side, `DimensionOutcome.status` is forced to `"unknown"` (`conclusion_kind="unresolved"`, `left_count=None`, `right_count=None`), and `DifferentialReport.overall_status` cannot be `"unchanged"` (`differential_facet.py:160-162`).
- [ ] **Graceful Single-Provider Degradation:**
  - When one of the two requested external binaries is not installed on the host, `harness rea diff` does not crash: it marks that provider's unavailable dimensions as `FacetAvailability(available=False, reason="provider '<name>' not installed")`, emits the resulting `"unknown"` dimension outcomes explicitly in the table, and labels the report with a top-level `degraded_single_provider` limitation notice.

---

## Track 6 — Control-Room API Route, UI Panel, and MCP Resources

- [ ] **FastAPI Control-Room Route (`src/harness/ui/server/routes/rea.py`):**
  - Follow the exact pattern of `src/harness/ui/server/routes/knowledge.py` and `skills.py`: add `/api/rea/providers`, `/api/rea/tools`, and `POST /api/rea/inspect` (accepting a workspace-confined artifact path) returning the serialized `DissectionEnvelope`.
  - Mount the router in `src/harness/ui/server/app.py` and add a lightweight REA Inspector view/link in the static control-room dashboard (`src/harness/ui/static/`) with zero new frontend dependencies.
- [ ] **MCP Server Surfacing (`src/harness/mcp/server/registry.py` — Code-Verified):**
  - *Verified during redraft:* `MCPMethodRouter._handle_tools_list` (`src/harness/mcp/server/router.py:67-69`) **already** exposes all `ToolRegistry` tools via `self.registry.tool_registry.to_mcp_tools(enabled_only=False)`, and `_handle_tools_call` (`router.py:71-85`) dispatches them via `tool_registry.invoke()`.
  - Add two read-only MCP resources in `MCPRegistry.list_resources()` / `read_resource()` (`src/harness/mcp/server/registry.py:52-125`):
    - `harness://rea/providers` — JSON status of external RE binaries (`ghidra`, `jadx`, `adb`, `wabt`, `wakaru`, `binwalk`, `unblob`).
    - `harness://rea/routing-table` — JSON artifact-kind routing matrix and canonical `rea.*` alias map.

---

## Track 7 — Canonical `rea.*` Tool Aliases, Docs, and Drift Gates

- [ ] **Data-Driven `rea.*` Alias Layer in `ToolRegistry` (`src/harness/services/tools/registry.py`):**
  - Add `_aliases: dict[str, str]` and `register_alias(alias: str, target: str)` to `ToolRegistry` so `get()`, `get_tool()`, `has_tool()`, `__contains__()`, `enable_tool()`, `disable_tool()`, `toggle_tool()`, and `invoke()` transparently resolve aliases while `list_tools()` / `get_schemas()` emit only canonical `ToolSpec` entries (preventing duplicate tool bloat in LLM context windows!).
  - Define the authoritative 28-entry `REA_TOOL_ALIASES: dict[str, str]` table in `src/harness/services/rea_toolkit.py`:
    - `rea.js.recover_sources` → `plugin.rea_javascript.rea_javascript_recover_sources`
    - `rea.js.electron_inspect` → `plugin.rea_javascript.rea_javascript_electron_inspect`
    - `rea.js.web_observe` → `plugin.rea_javascript.rea_javascript_web_observe`
    - `rea.js.dotnet_inspect` → `plugin.rea_javascript.rea_javascript_dotnet_inspect`
    - `rea.js.har_inspect` → `plugin.rea_javascript.rea_javascript_har_inspect`
    - `rea.managed.inspect_artifact` → `plugin.rea_managed_runtime.rea_inspect_managed_artifact`
    - `rea.managed.native_boundaries` → `plugin.rea_managed_runtime.rea_inspect_managed_native_boundaries`
    - `rea.managed.il2cpp_metadata` → `plugin.rea_managed_runtime.rea_inspect_il2cpp_metadata`
    - `rea.managed.model_artifact` → `plugin.rea_managed_runtime.rea_inspect_model_artifact`
    - `rea.managed.python_pyc` → `plugin.rea_managed_runtime.rea_inspect_python_pyc`
    - `rea.mobile.apk_inspect` → `plugin.rea_mobile_firmware.rea_mobile_apk_inspect`
    - `rea.mobile.jadx_decompile` → `plugin.rea_mobile_firmware.rea_mobile_jadx_decompile`
    - `rea.mobile.search_classes` → `plugin.rea_mobile_firmware.rea_mobile_android_search_classes`
    - `rea.mobile.trace_references` → `plugin.rea_mobile_firmware.rea_mobile_android_trace_references`
    - `rea.adb.inspect_client` → `plugin.rea_mobile_firmware.rea_mobile_adb_inspect_client`
    - `rea.adb.list_devices` → `plugin.rea_mobile_firmware.rea_mobile_adb_list_devices`
    - `rea.adb.list_packages` → `plugin.rea_mobile_firmware.rea_mobile_adb_list_packages`
    - `rea.adb.pull_package` → `plugin.rea_mobile_firmware.rea_mobile_adb_pull_package`
    - `rea.adb.read_logcat` → `plugin.rea_mobile_firmware.rea_mobile_adb_read_logcat`
    - `rea.firmware.inspect_regions` → `plugin.rea_mobile_firmware.rea_firmware_regions_inspect`
    - `rea.firmware.extract` → `plugin.rea_mobile_firmware.rea_firmware_extract`
    - `rea.native.batch_decompile` → `plugin.rea_native.rea_native_batch_decompile`
    - `rea.native.call_graph` → `plugin.rea_native.rea_native_call_graph`
    - `rea.native.elf_layout` → `plugin.rea_native.rea_native_elf_layout`
    - `rea.native.wasm_inspect` → `plugin.rea_native.rea_native_wasm_inspect`
    - `rea.native.evm_interface` → `plugin.rea_native.rea_native_evm_interface`
    - `rea.native.annotate_function` → `plugin.rea_native.rea_native_annotate_function`
    - `rea.native.inspect_load_image` → `plugin.rea_native.rea_native_inspect_load_image`
- [ ] **Diátaxis Documentation & Plugin Front-Door Links (`Rule 47`):**
  - Author `docs/how-to/use-rea-toolkit.md` covering the unified facade, `harness rea` CLI commands, the 3-valued availability & absence-claimability model, `rea diff` + `rea learn`, external provider installation, and the 28-row `REA_TOOL_ALIASES` reference table.
  - Update the 4 REA plugin `README.md` files and `docs/reference/cli.md` to reference `harness rea` and `docs/how-to/use-rea-toolkit.md` via relative links (`Rule 47`).
- [ ] **Automated Drift Gate (`tests/test_rea_toolkit_doc_drift.py`):**
  - Assert that:
    1. Every subcommand documented in `docs/how-to/use-rea-toolkit.md` and `docs/reference/cli.md` exists in `rea_group.commands`.
    2. Every target in `REA_TOOL_ALIASES` (28 aliases) matches an actual entrypoint in the 4 REA `plugin.json` manifests.
    3. Static markdown link linting passes with zero broken relative links (`Rule 47`).

---

## Track 8 — Hardening & Contract Verification Suite (`Rule 28`, `Rule 43`)

- [ ] **Synthetic Binary Fixture Matrix (`tests/test_service_rea_toolkit.py`):**
  - Generate tiny, deterministic, synthetic byte fixtures in `tmp_path` (never real malware or external binaries):
    - Minimal 64-bit ELF header (`\x7fELF\x02\x01\x01...`)
    - Minimal Native PE32+ (`MZ` + `PE\0\0` with CLR RVA = 0) vs Managed .NET PE32 (`MZ` + `PE\0\0` with non-zero CLR RVA)
    - Minimal DOS MZ image (`MZ` without `PE\0\0`)
    - Minimal APK ZIP (`PK\x03\x04` with `AndroidManifest.xml` and `classes.dex` header)
    - Minimal WASM module (`\x00asm\x01\x00\x00\x00`)
    - Minimal GGUF v3 header (`GGUF\x03\x00\x00\x00...`) and `.safetensors` header
    - Minimal Unity IL2CPP header (`0xFAB11BAF` + version 29)
    - Minimal CPython `.pyc` header + marshaled code object
    - Minimal Electron `.asar` header, `.har` capture JSON, `.js` bundle, and EVM hex string (`0x6080604052...`)
  - Assert 100% routing accuracy across all 13 artifact kinds and verify `DissectionEnvelope` immutability (`with pytest.raises((AttributeError, TypeError))` per `Rule 43`).
- [ ] **Provider-Missing & Budget-Truncation Matrix (`tests/test_command_rea.py`):**
  - Patch provider binary paths to `None` (`ghidra`, `jadx`, `adb`, `wabt`, `binwalk`, `unblob`) and assert every `harness rea` subcommand exits cleanly (`exit_code == 0`), reports `state: "unknown"` with a non-empty `reason`, and never fabricates empty `"absent"` claims.
  - Test budget truncation (`max_symbols=2`, `max_records=5`) and assert `coverage.truncated is True`, `coverage.absence_claimable is False`, and empty facets downgrade from `"absent"` to `"unknown"`.
- [ ] **Offline & Trust-Boundary Verification:**
  - Run HAR and JS bundle dissection under `HARNESS_NO_NETWORK=1` socket interception (`Rule 56`, preserving loopback `127.0.0.1` for Windows `ProactorEventLoop`) asserting zero outbound network calls.
  - Assert that `harness rea learn` never persists raw binary bytes or credential-like tokens (`Authorization:`, `Bearer`, API keys from HAR headers) into `.harness/knowledge/<ki_id>/`.

---

## Suggested Execution Order (The Pick Queue)

1. **Track 0 + Track 2 (Foundations + Unified `service.rea_toolkit` Facade):** Settle shared `FacetAvailability` imports with `differential_facet.py` / `reconstruction_obligation.py`, build the 13-kind artifact router, implement the `Rule 58` `SandboxedPlugin` / in-process adapter, and enforce `config.default.yaml` budgets.
2. **Track 1 (`harness rea` CLI Group):** Expose `inspect`, `list`, `providers`, `decompile`, `callgraph`, `signatures`, and `devices` with `--json` and mandatory availability output.
3. **Track 5 (`harness rea diff`):** Wire live multi-provider dissection into `StandardDifferentialFacetService.compare_observations()`.
4. **Track 4 (`harness rea learn` & `learned`):** Wire semantic signature extraction into `ReconstructionObligationService.ingest_evidence()` (`ev:<sha256>`) and the Knowledge Vault dual-file persistence pipeline (`Rule 40`).
5. **Track 3 (`rea-reverse-engineering` Skill):** Scaffold `SKILL.md` + `CARD.md` (`Rule 37`, `Rule 44`) and link into `differential-facet-verifier` and `reconstruction-obligation-ledger` (`Rule 47`, `Rule 55`).
6. **Track 7 (Aliases + Docs + Drift Gate):** Add non-duplicating tool alias resolution to `ToolRegistry`, register the 28 `rea.*` aliases, author `docs/how-to/use-rea-toolkit.md`, and lock with `test_rea_toolkit_doc_drift.py`.
7. **Track 6 (Control-Room Route + MCP Resources):** Add `/api/rea/*` routes and `harness://rea/*` MCP resources.
8. **Track 8 (Hardening):** Complete the 13-fixture routing matrix, provider-missing tests, budget truncation tests, and network/secret boundary assertions.

---

## §11 Verification Ledger (Resolved vs Remaining Runtime Checks)

- [x] **Verified (Code Read 2026-10-31): Which code executes a manifest-mounted REA tool call?**
  - `PluginLoader._load_manifest_plugin` (`src/harness/plugins/loader.py:329-349`) wraps any plugin with `"isolation": "subprocess"` in `SandboxedPlugin` (`src/harness/plugins/sandboxed.py:69`). On `on_load`, `SandboxedPlugin` provides `self` under the `ServiceKey`; on `on_enable`, it mounts `ToolSpec`s that call `self.invoke_typed()`, spawning `bridge_runner.py` in a subprocess against the top-level functions in `main.py`. Therefore, `resolve_rea_toolkit()` must include a `Rule 58` adapter supporting both `SandboxedPlugin.invoke_typed` and direct `Rea*Service` protocol methods.
- [x] **Verified (Code Read 2026-10-31): Does `HarnessMCPServer` expose `ToolRegistry` tools generically over `tools/list`?**
  - Yes. `MCPMethodRouter._handle_tools_list` (`src/harness/mcp/server/router.py:67-69`) calls `self.registry.tool_registry.to_mcp_tools(enabled_only=False)`, and `_handle_tools_call` (`router.py:71-85`) invokes `self.registry.tool_registry.invoke()`. All 28 REA tools are automatically MCP-callable once mounted; Track 6 adds `harness://rea/providers` and `harness://rea/routing-table` as MCP resources.
- [x] **Verified (Code Read 2026-10-31): Do existing skills or services already cover REA semantics?**
  - Yes! `src/harness/services/differential_facet.py` (`harness facet`, `.agents/skills/differential-facet-verifier/`) and `src/harness/services/reconstruction_obligation.py` (`harness rol`, `.agents/skills/reconstruction-obligation-ledger/`) already implement `FacetAvailability`, `CoverageDeclaration.absence_claimable`, `DifferentialReport` (`rep:<sha256>`), and `CanonicalEvidence` (`ev:<sha256>`). Furthermore, `plugins/security_and_forensics/magika_content_detector/` and `magika_format_forensics/` already provide content detection and polyglot/extension-spoofing checks. The plan now composes these services rather than duplicating them.
- [ ] **Runtime Check (Execute in Track 1/8):** Measure live external binary presence (`ghidra`, `jadx`, `adb`, `wasm2wat`, `wakaru`, `binwalk`, `unblob`) on the Windows dev machine via `harness rea providers` and record the baseline output.
- [ ] **Runtime Check (Execute in Track 7/8):** Verify `harness tool list --provider plugin.rea_native` (and all 4 REA providers) plus `rea.*` alias invocation end-to-end through `HarnessRuntime`.
