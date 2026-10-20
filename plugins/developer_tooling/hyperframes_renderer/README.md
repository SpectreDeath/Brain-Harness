# HyperFrames Renderer Plugin

Programmatic multimedia video rendering plugin bridging the HeyGen HyperFrames Node.js/TypeScript engine into the Brain Harness IoC micro-kernel.

## Features
- **Slotted Data Models:** Strict typed dataclasses for `VideoScene`, `RenderRequest`, and `RenderOutput`.
- **Subprocess Isolation:** JSON-RPC execution adhering to Rule 14 (pipe drainage) and Rule 56 (loopback preservation).
- **Headless Fallback Simulation:** Pure Python fallback for CI test runners where Node or browser runtimes are absent.
- **Agent Visual Trajectories:** Transforms execution step graphs and PR diffs into dynamic video presentations.
