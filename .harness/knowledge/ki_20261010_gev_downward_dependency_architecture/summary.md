# Downward-Only Tool Boundary Architecture & Package Isolation Invariant

## Architectural Thesis
In complex multimodal AI applications blending browser 3D rendering (CesiumJS, Three.js) with voice agents and Model Context Protocol (MCP) servers, tool implementations easily degrade if they import DOM globals, browser contexts, or heavy visualization rendering state. 

God's Eye View (`gods-eye-view`) enforces a strict **downward-only dependency invariant**:
1. Tool definitions (`src/tools/`) and domain query handlers (`src/tools/queries/`) read only portable service contracts and abstract data sources.
2. Tools never import Cesium, window/document DOM globals, or Node filesystem globals directly.
3. Automated AST package boundary linters (`scripts/check-package-boundaries.mjs` and `scripts/check-import-directions.mjs`) fail CI if any tool introduces upward dependencies into the UI or application lifecycle layers.

## Provenance & Isnad Lineage
- Primary source: `D:\GitHub\cloned\gods-eye-view\scripts\check-package-boundaries.mjs`
- Core catalog: `D:\GitHub\cloned\gods-eye-view\src\tools\catalog.js`
- Tools architecture doc: `D:\GitHub\cloned\gods-eye-view\docs\TOOLS.md`

## Application to Brain Harness
Brain Harness plugins follow this exact discipline under Rule 18 (Domain-Partitioned Plugin Synthesis) and Rule 49 (Skill-to-IoC Micro-Kernel Seam Elevation). Geospatial query tools execute cleanly in headless, sandboxed CLI environments without browser window requirements.
