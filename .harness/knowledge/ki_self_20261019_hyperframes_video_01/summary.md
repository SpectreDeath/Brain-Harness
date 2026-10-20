# Programmatic Motion Graphics Rendering via Node.js Subprocess JSON-RPC

## Executive Summary
This Knowledge Item establishes the architectural patterns and invariants governing the integration of external Node.js/TypeScript motion-graphics renderers (HeyGen HyperFrames) into the Python micro-kernel. It codifies the separation between slotted immutable domain definitions and the headless JSON-RPC bridge.

## Architectural Seams & Invariants

1. **Subprocess Isolation & Transport Hygiene (Rule 14 & Rule 56):**
   - Subprocess execution communicates via JSON-RPC payloads over stdin/stdout.
   - Standard error is drained concurrently into a bounded ring buffer (`deque(maxlen=50)`).
   - All standard stream pipes are cleanly closed in `finally` blocks to prevent Windows proactor event loop leaks.
   - Loopback connections (`127.0.0.1`, `localhost`, `::1`) are strictly preserved in proxy configurations.

2. **Zero-Install Headless CI Simulation:**
   - When Node.js or `@heygen/hyperframes` is absent on the host environment, the bridge transparently switches to simulated rendering mode.
   - Generates deterministic JSON trajectory manifests and HTML bundles, permitting full test suite execution without external runtime dependencies.

3. **Slotted Domain Models (Rule 12 & Rule 43):**
   - `VideoScene`: immutable scene definitions with validated durations ($> 0$), transition tags (`fade`, `slide`, `zoom`), and HTML/GSAP payloads.
   - `RenderRequest`: validated scenes tuple, frame rate bounds ($1 \le \text{fps} \le 120$), and dual-dimension resolution.
   - `RenderOutput`: deterministic metrics tracking artifact path, frame counts, size bytes, and render duration.
