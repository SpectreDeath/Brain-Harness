# REA JavaScript & Web Forensics Plugin (`plugin.rea_javascript`)

## Overview

Part of the REA multi-capability reverse engineering bridge into Brain Harness.
Provides JavaScript source recovery and deobfuscation via Wakaru `^1.13.0`,
Electron ASAR archive unpacking and IPC channel discovery, passive Chrome DevTools Protocol
(CDP) DOM and script observation, .NET managed assembly inspection, and offline HAR capture analysis.

- **Category:** `data_engineering`
- **Service Key:** `service.rea_javascript`
- **Isolation Mode:** `IsolationMode.SUBPROCESS` (Rule 5)
- **Source Repository:** `https://github.com/morluto/rea` (Commit: `166dcd21`)

## Exported Tools

1. `rea_javascript_recover_sources(bundle_path, output_dir, sourcemap_path=None)`
2. `rea_javascript_electron_inspect(asar_path, extract_ipc=True)`
3. `rea_javascript_web_observe(cdp_endpoint, target_id=None, duration_ms=10000)`
4. `rea_javascript_dotnet_inspect(assembly_path, include_cil=True)`
5. `rea_javascript_har_inspect(har_path, filter_status=None)`

## Operational Budgets (`config.default.yaml`)

- `subprocess_timeout_s`: 120
- `wakaru_max_input_bytes`: 67,108,864 (64 MiB)
- `wakaru_max_output_entries`: 10,000
- `cdp_observation_timeout_s`: 30


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `rea_javascript_recover_sources` | `(bundle_path, output_dir, sourcemap_path)` | Recover module directory trees and source maps from minified/bundled scripts via Wakaru ^1.13.0. |
| `rea_javascript_electron_inspect` | `(asar_path, extract_ipc)` | Inspect Electron ASAR archives: manifest, processes, preload scripts, and declared IPC event channels. |
| `rea_javascript_web_observe` | `(cdp_endpoint, target_id, duration_ms)` | Passive Chrome DevTools Protocol observation of page DOM structure, loaded scripts, event listeners, and network activity. |
| `rea_javascript_dotnet_inspect` | `(assembly_path, include_cil)` | Open a managed .NET PE/CLI image: inventory type hierarchies, CIL hashes, and P/Invoke declarations. |
| `rea_javascript_har_inspect` | `(har_path, filter_status)` | Inspect offline HAR 1.2 or native mitmproxy capture records without contacting recorded servers. |
