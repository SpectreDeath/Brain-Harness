# Deterministic Artifact-Type Routing Matrix

The REA toolkit routes inspection targets across 13 artifact categories based on deterministic magic bytes, file container structures, and header fields:

| Artifact Kind | Detection Rule | Target Engine / Plugin | Primary Facet Operations |
|---|---|---|---|
| **ELF** | Magic `\x7fELF` at offset 0 | `plugin.rea_native` | `elf_layout`, `batch_decompile`, `call_graph` |
| **PE Managed** | `MZ` at 0, `PE\0\0`, and Optional Header Data Directory #14 (CLR RVA) > 0 | `plugin.rea_managed_runtime` | `inspect_managed_artifact`, `inspect_managed_native_boundaries`, `dotnet_inspect` |
| **PE Native** | `MZ` at 0, `PE\0\0`, and CLR RVA == 0 | `plugin.rea_native` | `elf_layout`, `batch_decompile`, `call_graph` |
| **DOS MZ** | `MZ` at 0 without valid `PE\0\0` signature | `plugin.rea_native` | `inspect_load_image` |
| **APK** | ZIP archive (`PK\x03\x04`) containing `AndroidManifest.xml` or `.apk` suffix | `plugin.rea_mobile_firmware` | `apk_inspect`, `jadx_decompile`, `android_search_classes` |
| **ASAR** | Chromium pickle header with `{"files": ...}` or `.asar` suffix | `plugin.rea_javascript` | `electron_inspect` (IPC channels, manifest) |
| **WASM** | Magic `\x00asm\x01\x00\x00\x00` at offset 0 or `.wasm` suffix | `plugin.rea_native` | `wasm_inspect` (WABT sections, imports, exports) |
| **IL2CPP Metadata** | Magic `\xaf\x1b\xb1\xfa` (0xFAB11BAF) or `global-metadata.dat` | `plugin.rea_managed_runtime` | `inspect_il2cpp_metadata` (versions 24, 27, 29, 31, 39) |
| **AI Model Weights** | Magic `GGUF` at offset 0 (`.gguf`) or 8-byte uint64 JSON header size (`.safetensors`) | `plugin.rea_managed_runtime` | `inspect_model_artifact` (zero-allocation seeks) |
| **CPython Bytecode** | Magic tag `\r\n` at offsets 2-4 or `.pyc` suffix | `plugin.rea_managed_runtime` | `inspect_python_pyc` (3.7-3.13 opcode disassembly) |
| **HAR Capture** | JSON root with `log.version` and `log.entries` or `.har` suffix | `plugin.rea_javascript` | `har_inspect` (passive offline requests/responses) |
| **JavaScript Bundle** | Minified script heuristics or `.js`/`.mjs`/`.cjs` suffix | `plugin.rea_javascript` | `recover_sources` (Wakaru ^1.13.0 deobfuscation) |
| **EVM Bytecode** | `0x`-prefixed or raw hex string matching EVM opcodes | `plugin.rea_native` | `evm_interface` (4-byte selectors, ABI resolution) |
| **Firmware Blob** | Magic `hsqs`/`sqsh` or `.bin`/`.fw` suffix | `plugin.rea_mobile_firmware` | `firmware_inspect_regions` (Binwalk / Unblob) |

