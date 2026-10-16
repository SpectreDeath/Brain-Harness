# REA Native Inspection Plugin (`plugin.rea_native`)

## Overview

Part of the REA multi-capability reverse engineering bridge into Brain Harness.
Provides native binary inspection, disassembly, decompilation, call graph tracing,
exploit mitigation checking, WebAssembly inspection via WABT 1.0.42, and EVM bytecode interface parsing.

- **Category:** `security_and_forensics`
- **Service Key:** `service.rea_native`
- **Isolation Mode:** `IsolationMode.SUBPROCESS` (Rule 5)
- **Source Repository:** `https://github.com/morluto/rea` (Commit: `ffaf2c12`)

## Exported Tools

1. `rea_native_batch_decompile(target_path, symbols, provider="ghidra")`
2. `rea_native_call_graph(target_path, entry_symbol, depth=3, direction="callee")`
3. `rea_native_elf_layout(target_path, checksec=True)`
4. `rea_native_wasm_inspect(wasm_path, emit_wat=True)`
5. `rea_native_evm_interface(bytecode_hex, resolve_signatures=True)`
6. `rea_native_annotate_function(target_path, address, name=None, comment=None)`
7. `rea_native_inspect_load_image(target_path)`

## Operational Budgets (`config.default.yaml`)

- `subprocess_timeout_s`: 120
- `max_symbols_per_batch`: 50
- `decompile_retry_limit`: 2
- `wasm_max_input_bytes`: 8,388,608 (8 MiB)
- `wasm_max_output_bytes`: 33,554,432 (32 MiB)
- `wasm_deadline_s`: 30


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `rea_native_batch_decompile` | `(target_path, symbols, provider)` | Decompile one or more procedure symbols concurrently via headless Ghidra, Hopper, or IDA. |
| `rea_native_call_graph` | `(target_path, entry_symbol, depth, direction)` | Traverse caller or callee relationships from a procedure entrypoint. |
| `rea_native_elf_layout` | `(target_path, checksec)` | Offline static binary inspection via pwntools: section map, imported/exported symbols, and exploit mitigations (checksec). |
| `rea_native_wasm_inspect` | `(wasm_path, emit_wat)` | Validate and inspect WebAssembly binaries via WABT 1.0.42: sections, imports/exports, and optional WAT disassembly. |
| `rea_native_evm_interface` | `(bytecode_hex, resolve_signatures)` | Parse flat EVM bytecode, extract 4-byte dispatch selectors, disassemble opcodes, and resolve public ABI signatures. |
| `rea_native_annotate_function` | `(target_path, address, name, comment)` | Atomically update a function name and/or entry comment in the Ghidra session database. |
| `rea_native_inspect_load_image` | `(target_path)` | Verify a loaded DOS MZ or COM image against its immutable target snapshot: byte digests, header mappings, and relocations. |
