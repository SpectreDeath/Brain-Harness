# How-To: Inspect and Reverse Engineer Binaries with the REA Toolkit

This guide explains how to use the REA (Reverse-Engineering Automation) unified toolkit across the headless Click CLI (`harness rea`), the agent skill (`rea-reverse-engineering`), the IoC micro-kernel service seam (`ReaToolkitService`), REST API endpoints, and MCP resources.

---

## 1. Overview & Architecture

The REA toolkit provides a single-seam facade over four specialized domain plugins:
1. `plugin.rea_native`: ELF, Native PE/COFF, DOS MZ/COM, WebAssembly (WABT), and EVM bytecode inspection, batch decompilation, and call graphs.
2. `plugin.rea_managed_runtime`: .NET PE/CLI assemblies, Unity IL2CPP `global-metadata.dat`, AI models (GGUF / Safetensors), and CPython `.pyc` bytecode disassembly.
3. `plugin.rea_mobile_firmware`: Android APK packages, Dalvik bytecode decompilation (JADX), ADB client and device interaction, and firmware region carving (Binwalk / Unblob).
4. `plugin.rea_javascript`: Source-map and bundle source recovery (Wakaru), Electron ASAR extraction, passive CDP web observation, and offline HAR capture inspection.

### Architectural Invariants
- **Subprocess Isolation**: Underlying domain engines remain isolated in dedicated subprocess sandboxes.
- **Availability Semantics**: Every facet reports one of 4 explicit states: `AVAILABLE`, `ABSENT`, `UNKNOWN`, or `UNSUPPORTED`.
- **Absence Claimability Gate**: Negative conclusions (e.g. "binary has no exports") are only claimable if `coverage.absence_claimable is True` (non-truncated, non-polyglot, tool claimed full capability).
- **Non-Duplicating Aliasing**: 28 canonical `rea.*` tool aliases route transparently into native plugin identifiers without bloating model tool schemas.
- **Endogenous Learn Loop**: Every dissection can be permanently retained as immutable `ev:<sha256>` evidence and sealed into the Knowledge Vault (`.harness/knowledge/<ki_id>/`).

---

## 2. Headless CLI Reference (`harness rea`)

The CLI group `harness rea` provides 10 headless subcommands:

### 2.1 `harness rea inspect <target>`
Auto-detects the target's artifact category, checks polyglot indicators, dispatches to the primary domain engine, and displays section layouts, headers, and semantic signatures:

```bash
# Inspect a native binary or library
harness rea inspect /path/to/libtarget.so

# Inspect with custom symbol and record budgets
harness rea inspect app.wasm --max-symbols 500 --max-records 1000

# Output structured JSON
harness rea inspect app.apk --json
```

### 2.2 `harness rea list`
Enumerates all 28 REA tools organized by artifact category along with their canonical alias and target plugin:

```bash
harness rea list
```

### 2.3 `harness rea providers`
Audits the health, version, isolation status, and registered tool counts of the 4 underlying REA domain plugins:

```bash
harness rea providers
```

### 2.4 `harness rea decompile <target>`
Decompiles functions in native binaries or Dalvik classes in Android APKs:

```bash
# Decompile native function via headless Ghidra/Hopper/IDA
harness rea decompile /path/to/binary --function main

# Decompile specific Android class via JADX
harness rea decompile target.apk --class-name com.example.MainActivity
```

### 2.5 `harness rea callgraph <target>`
Generates caller/callee call-graph relationships for target functions:

```bash
harness rea callgraph /path/to/binary --function crypto_encrypt --depth 3
```

### 2.6 `harness rea signatures <target>`
Extracts semantic signatures (cryptographic constants, network endpoints, exported API symbols, dangerous sinks, and capability indicators):

```bash
harness rea signatures /path/to/firmware.bin --category crypto
```

### 2.7 `harness rea devices`
Inspects local ADB client status, version, and lists connected physical Android devices or emulators:

```bash
harness rea devices
```

### 2.8 `harness rea diff <target>`
Executes multi-provider differential analysis across two distinct domain tools or mock providers:

```bash
harness rea diff /path/to/binary --providers plugin.rea_native,mock_provider
```

Outputs a 3-valued differential outcome (`EQUAL`, `DIFFERENT`, `DEGRADED`) across dimensions.

### 2.9 `harness rea learn <target>`
Synthesizes findings from an inspection target, seals immutable `ev:<sha256>` CanonicalEvidence, and authors a dual-file Knowledge Item (`metadata.json` + `summary.md`) in `.harness/knowledge/`:

```bash
# Dry run verification
harness rea learn target.wasm --dry-run

# Commit permanently to Knowledge Vault
harness rea learn target.wasm --domain reverse_engineering --tag webassembly --tag security
```

### 2.10 `harness rea learned`
Lists all reverse-engineering Knowledge Items stored in the Knowledge Vault:

```bash
harness rea learned
```

---

## 3. Artifact Routing & Category Matrix

The 13 supported artifact categories are automatically detected by magic header bytes, file suffixes, and PE/CLI header analysis:

| Category | Typical Suffixes | Magic Bytes / Header | Primary Plugin | Secondary Plugins |
|---|---|---|---|---|
| `elf` | `.so`, `.elf`, `.o`, `.bin` | `\x7fELF` | `plugin.rea_native` | - |
| `pe_managed` | `.exe`, `.dll` | `MZ` + CLR Header RVA > 0 | `plugin.rea_managed_runtime` | `plugin.rea_javascript`, `plugin.rea_native` |
| `pe_native` | `.exe`, `.dll`, `.sys` | `MZ` + CLR Header RVA == 0 | `plugin.rea_native` | - |
| `dos_mz` | `.exe`, `.com` | `MZ` (no PE signature) | `plugin.rea_native` | - |
| `apk` | `.apk`, `.xapk` | `PK\x03\x04` + `AndroidManifest.xml` | `plugin.rea_mobile_firmware` | - |
| `asar` | `.asar` | `\x04\x00\x00\x00` JSON header | `plugin.rea_javascript` | - |
| `wasm` | `.wasm` | `\x00asm` (v1) | `plugin.rea_native` | - |
| `il2cpp_metadata` | `.dat`, `global-metadata.dat` | `\xaf\x1b\xb1\xfa` | `plugin.rea_managed_runtime` | - |
| `ai_model` | `.gguf`, `.safetensors` | `GGUF` or uint64 header | `plugin.rea_managed_runtime` | - |
| `cpython_pyc` | `.pyc` | Magic uint32 (PEP 552) | `plugin.rea_managed_runtime` | - |
| `har` | `.har`, `.json` | `{"log": ...}` | `plugin.rea_javascript` | - |
| `javascript_bundle` | `.js`, `.mjs`, `.bundle` | JS text tokens | `plugin.rea_javascript` | - |
| `evm_bytecode` | `.bin`, `.hex`, `.evm` | EVM dispatcher `60806040` | `plugin.rea_native` | - |
| `firmware` | `.bin`, `.img`, `.rom` | Multi-region header | `plugin.rea_mobile_firmware` | - |

---

## 4. Authoritative 28-Entry Tool Alias Mapping

When invoking tools through `ToolRegistry` or agent ReAct loops, use either the unified `rea.*` alias or the underlying plugin tool name:

```
JavaScript & Web:
  rea.js.recover_sources      -> plugin.rea_javascript.rea_javascript_recover_sources
  rea.js.electron_inspect     -> plugin.rea_javascript.rea_javascript_electron_inspect
  rea.js.web_observe          -> plugin.rea_javascript.rea_javascript_web_observe
  rea.js.dotnet_inspect       -> plugin.rea_javascript.rea_javascript_dotnet_inspect
  rea.js.har_inspect          -> plugin.rea_javascript.rea_javascript_har_inspect

Managed Runtime:
  rea.managed.inspect_artifact    -> plugin.rea_managed_runtime.rea_inspect_managed_artifact
  rea.managed.native_boundaries   -> plugin.rea_managed_runtime.rea_inspect_managed_native_boundaries
  rea.managed.il2cpp_metadata     -> plugin.rea_managed_runtime.rea_inspect_il2cpp_metadata
  rea.managed.model_artifact      -> plugin.rea_managed_runtime.rea_inspect_model_artifact
  rea.managed.python_pyc          -> plugin.rea_managed_runtime.rea_inspect_python_pyc

Mobile & Firmware:
  rea.mobile.apk_inspect          -> plugin.rea_mobile_firmware.rea_mobile_apk_inspect
  rea.mobile.jadx_decompile       -> plugin.rea_mobile_firmware.rea_mobile_jadx_decompile
  rea.mobile.search_classes       -> plugin.rea_mobile_firmware.rea_mobile_android_search_classes
  rea.mobile.trace_references     -> plugin.rea_mobile_firmware.rea_mobile_android_trace_references
  rea.adb.inspect_client          -> plugin.rea_mobile_firmware.rea_mobile_adb_inspect_client
  rea.adb.list_devices            -> plugin.rea_mobile_firmware.rea_mobile_adb_list_devices
  rea.adb.list_packages           -> plugin.rea_mobile_firmware.rea_mobile_adb_list_packages
  rea.adb.pull_package            -> plugin.rea_mobile_firmware.rea_mobile_adb_pull_package
  rea.adb.read_logcat             -> plugin.rea_mobile_firmware.rea_mobile_adb_read_logcat
  rea.firmware.inspect_regions    -> plugin.rea_mobile_firmware.rea_firmware_regions_inspect
  rea.firmware.extract            -> plugin.rea_mobile_firmware.rea_firmware_extract

Native Binaries:
  rea.native.batch_decompile      -> plugin.rea_native.rea_native_batch_decompile
  rea.native.call_graph           -> plugin.rea_native.rea_native_call_graph
  rea.native.elf_layout           -> plugin.rea_native.rea_native_elf_layout
  rea.native.wasm_inspect         -> plugin.rea_native.rea_native_wasm_inspect
  rea.native.evm_interface        -> plugin.rea_native.rea_native_evm_interface
  rea.native.annotate_function    -> plugin.rea_native.rea_native_annotate_function
  rea.native.inspect_load_image   -> plugin.rea_native.rea_native_inspect_load_image
```

---

## 5. Control Room REST & MCP Seams

### REST API
- `GET /api/rea/providers`: Returns provider status, versions, and capabilities.
- `GET /api/rea/tools`: Returns the catalog of REA tools grouped by category.
- `POST /api/rea/inspect`: Performs artifact detection and dissection for a given file path.

### MCP Resources
- `harness://rea/providers`: Real-time JSON health report of all 4 domain providers.
- `harness://rea/routing-table`: Declarative JSON routing table mapping artifact categories to primary and secondary plugin IDs, magic signatures, and typical extensions.

---

## 6. Related Resources
- Agent Skill: [rea-reverse-engineering](../../.agents/skills/rea-reverse-engineering/SKILL.md)
- CLI Reference: [CLI Reference](../reference/cli.md)
- Domain Plugins:
  - [rea_native](../../plugins/security_and_forensics/rea_native/README.md)
  - [rea_managed_runtime](../../plugins/security_and_forensics/rea_managed_runtime/README.md)
  - [rea_mobile_firmware](../../plugins/security_and_forensics/rea_mobile_firmware/README.md)
  - [rea_javascript](../../plugins/data_engineering/rea_javascript/README.md)

