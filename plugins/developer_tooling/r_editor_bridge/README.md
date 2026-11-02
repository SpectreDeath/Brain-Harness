# R Editor Bridge Plugin (`plugin.r_editor_bridge`)

## Overview
The `r_editor_bridge` plugin connects the Brain Harness micro-kernel to the official `REditorSupport` ecosystem (`languageserver`, `vscode-R`, `jgd`, `vscode-R-syntax`, `sublime-ide-r`).

It registers the `service.r_runtime` key (`R_RUNTIME_SERVICE_KEY`) in the IoC container and exposes tools for:
- Session inspection and workspace tracking without `.GlobalEnv` pollution.
- LSP 3.17 diagnostic parsing, position translation, and severity mapping.
- C-level `jgd` JSON graphics device event streaming.
- Safe subprocess execution with bounded stderr ring buffer and pipe disposal.

## Tools
- `r_inspect_session`: Retrieve active session status, namespaces, and device state.
- `r_parse_diagnostics`: Convert raw LSP/lintr messages into normalized diagnostics.
- `r_stream_plot`: Process graphics display-list packets.
- `r_validate_config`: Verify language server paths and debounce parameters.

