# C-Level R GEdevice Interception & Zero-Dependency JSON Graphics Streaming

## Context & Theoretical Grounding
Standard R graphics devices (e.g. `png()`, `pdf()`, `X11()`, `windows()`) either produce static raster/vector files requiring disk polling or depend on heavy OS GUI windowing loops. `jgd` provides a headless, zero-dependency C graphics device that serializes drawing primitives directly into structured JSON streams.

## Distilled Mental Models & Heuristics
1. **GEdevice Function Table Registration**:
   - `jgd` implements the standard R `pDevDesc` callbacks (`device.c`): `dev_mode`, `dev_metricInfo`, `dev_clip`, `dev_size`, `dev_strWidth`, `dev_text`, `dev_line`, `dev_circle`, `dev_polygon`, `dev_polyline`, `dev_rect`, `dev_raster`.
2. **Atomic Display-List Serialization**:
   - Rather than rendering pixels in C, each primitive is converted to a compact `cJSON` node and pushed into an in-memory display list buffer.
3. **Transport Decoupling**:
   - Inter-process communication operates over OS-native named pipes (Windows `\\.\pipe\...`) or Unix domain sockets (`transport.c`), feeding an external Deno/TypeScript hub (`hub.ts`) that broadcasts SVG/Canvas updates to IDE webviews via WebSockets.

## Anti-Pattern Defenses
- **Disk Polling for Plot Updates**: Relying on filesystem watchers over temporary PNG files which causes race conditions and file lock contention on Windows.
- **Heavy Headful GUI Dependencies**: Requiring GTK or Qt libraries in headless container environments just to capture R plots.
