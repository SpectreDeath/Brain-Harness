---
name: geospatial-disaster-simulation
description: Simulate real-world natural disasters on geospatial map tiles using tile-snapped canvas raster sources, Mercator elevation decoding, and Three.js 3D WebGL building collapse physics. Do not use for non-georeferenced 2D animations, static GIS styling, or purely synthetic particle physics.
---

# Geospatial Disaster Simulation: Real-Map Inundation & 3D Building Collapse Engine

`geospatial-disaster-simulation` is the authoritative simulation engineering skill for executing real-world natural disaster scenarios (tsunamis, riverine floods, and seismic structural collapses) on interactive web maps using Mapbox GL JS / MapLibre GL and Three.js.

Distilled from the engineering breakthroughs of **Alex Oliinyk** on [HazardSim](https://hazardsim.com/), this skill eliminates the **"Sticker Problem"** (naive screen-space canvas overlays that float, smear, and desynchronize when the camera tilts) by enforcing a strict **Dual-World Coordinate Architecture**:
1. **Ground Tier**: Tile-aligned canvas raster sources draped directly onto 3D terrain mesh.
2. **Height Tier**: Shared WebGL 3D context with `promoteId` feature-state extrusion scaling and Three.js instanced physics.

See [CARD.md](CARD.md) for the companion summary card, 5-stage progression matrix, and invariants checklist.
Consult [open-source-gis-architect](../open-source-gis-architect/SKILL.md) for raster GIS tooling, [python-dataclass-architect](../python-dataclass-architect/SKILL.md) for slotted domain models, and [epistemic-isnad-audit](../epistemic-isnad-audit/SKILL.md) for primary source provenance.

---

## The 5-Stage Simulation Pipeline

```
[1. Grid Ingestion & Elevation] ──► [2. Ground Fluid Canvas Draping] ──► [3. Footprint Extraction & Feature Scaling]
                                                                                           │
                                                                                           ▼
[5. Camera Choreography & Defense] ◄── [4. 3D WebGL Custom Layer & Instanced Debris] ◄─────┘
```

---

## 1. Geospatial Grid Ingestion & Tile Alignment

Map simulations must execute in map coordinates, not screen coordinates. Align computational grids directly to Web Mercator tile pyramids to consume external raster and elevation tiles without resampling:

1. **Web Mercator Coordinate Projection**:
   - Convert geographic bounds $(\text{lng}, \text{lat})$ to tile coordinates $(x, y)$ at zoom $z$:
     $$x = \frac{\text{lon} + 180}{360} \cdot 2^z$$
     $$y = \frac{1 - \ln(\tan(\text{rad}) + \sec(\text{rad})) / \pi}{2} \cdot 2^z$$
2. **Automated Budgeted Zoom Selection**:
   - Step zoom $z$ downward from 15 to 8 until bounding box dimensions satisfy operational budgets ($\le 780\text{ px}$ width and $\le 620,000\text{ cells}$).
   - Snap bounding box outward to integer tile coordinates $(x_0, y_0) \to (x_1, y_1)$ to guarantee exact 1-to-1 mapping with downloaded tiles.
   - Calculate metric cell resolution: $\text{cellM} = 156543.03392 \cdot \cos(\text{lat}) / 2^z$.
3. **Dual Elevation Tile Decoding**:
   - **AWS Terrarium PNGs** (S3 Open Data):
     $$\text{elev}_m = R \cdot 256 + G + \frac{B}{256} - 32768$$
   - **Mapbox Terrain-RGB**:
     $$\text{elev}_m = -10000 + (R \cdot 65536 + G \cdot 256 + B) \cdot 0.1$$
   - Ingest into a contiguous 1D `Float32Array`. Run a $3 \times 3$ median filter across neighbors differing by $> 8\text{ m}$ to eliminate single-pixel sensor spikes.
   - Identify sea cells: cells with $\text{elev} \le 0$ connected to the grid boundary via continuous water paths.

> **Completion Criterion**: 1D Float32Array elevation grid loaded, snapped to tile boundaries, spikes filtered, and cell resolution established.

---

## 2. Ground-Tier Fluid & Inundation Simulation

Ground fluids (tsunami surges, flood inundations, mudflows) must live on the ground surface, allowing automatic terrain draping, foreshortening, and rotation:

1. **Hydraulic Inundation Propagation**:
   - Execute breadth-first search (BFS) flood progression from source coastlines or rivers across cell elevation gradients.
   - Store reach timestamp $T_{\text{reach}}$ and water depth array per grid cell.
2. **Canvas Raster Source Attachment**:
   - Register an offscreen `<canvas>` with dimensions $W \times H$ as a Mapbox `canvas` source:
     ```javascript
     map.addSource("flood", {
       type: "canvas", canvas: "floodcanvas", coordinates: coords, animate: true
     });
     map.addLayer({
       id: "flood", type: "raster", source: "flood",
       paint: { "raster-opacity": 0.94, "raster-resampling": "linear", "raster-fade-duration": 0 }
     });
     ```
   - Mandatory flags: `animate: true` (forces per-frame texture re-upload), `"raster-resampling": "linear"` (smooth cell interpolation), `"raster-fade-duration": 0` (eliminates ghosting).
3. **Dual-Mask Video Texture Compositing**:
   - Avoid baking color into video textures; maintain neutral greyscale water footage.
   - Tint dynamically in a scratch buffer with time-ramped sediment interpolation (`mud` factor: $0 \to 1$).
   - Apply `destination-in` with `landMask` (white on land, transparent on open sea) to confine flood color to dry ground.
   - Composite onto the main flood canvas via `source-atop`, ensuring water texture is clipped strictly to the simulated flood boundary with zero per-pixel iteration.
4. **Local Seaward Camera Calculation**:
   - Locate the nearest coastline cell to the city center.
   - Average directional offsets to sea cells within a $2.5\text{ km}$ radius to determine true local seaward bearing $\theta_{\text{seaward}}$, preventing curved bay distortion.

> **Completion Criterion**: Dynamic canvas raster draped over terrain, compositing video textures within flood masks, and seaward camera vector computed.

---

## 3. Footprint Extraction & Dynamic Feature-State Scaling

Earthquake destruction requires differentiating between distance-based background buildings and foreground hero structures:

1. **Vector Footprint Extraction & GeoJSON Promotion**:
   - Ingest building footprints from vector tiles via `map.querySourceFeatures()`.
   - Deduplicate geometries across tile boundaries.
   - Copy features into a dedicated GeoJSON source configured with `promoteId: "i"` (where `i` is an integer index). Calling `map.setFeatureState()` on vector tile features silently fails because vector buildings lack feature IDs.
2. **Patterned Facade Extrusion Styling**:
   - Configure dual `fill-extrusion` layers (`bld-walls` and `bld-roof`).
   - Drive extrusion heights via feature-state multiplier $k$:
     ```javascript
     "fill-extrusion-height": ["*", ["get", "height"], ["feature-state", "k"]]
     ```
   - Insert building layers below the first `symbol` layer (`map.getStyle().layers`) so labels remain visible above roofs.
3. **Seismic Attenuation & Piecewise Fragility**:
   - Compute hypocentral distance: $R = \sqrt{r_{\text{km}}^2 + \text{depth}^2}$ (default depth: $10\text{ km}$).
   - Calculate Modified Mercalli Intensity:
     $$\text{MMI} = 1.5 M - 3.0 \log_{10}(R) - 0.0018 R + 1.6$$
   - Interpolate collapse probability $P_{\text{collapse}}$ across piecewise fragility curve:
     `[[6.5, 0], [7, 0.004], [8, 0.025], [9, 0.08], [10, 0.20], [11, 0.38], [12, 0.55]]`.
   - Scale probability by structural quality factor $q$ (strict=0.2, avg=1.0, poor=3.0) and height factor $h_f$ (mid-rise 15–35m most vulnerable).
4. **5-Mode Building Collapse Kinematics**:
   - Modulate $k(u)$ from $1.0$ down to rubble height $k_f$ across 5 distinct modes:
     1. *Floor-by-Floor*: Staircase drop and pause per floor level.
     2. *Soft-Storey*: Ground-floor drop, long pause, then rapid collapse.
     3. *Crushed Top*: Upper third fails early, pauses, then collapses lower sections.
     4. *Sideways*: Steady accelerating lean and sink.
     5. *Pancake*: Accelerating parabolic free fall ($k = k_0 - \Delta k \cdot u^2$).
   - Clamp frame delta time $\Delta t \le 40\text{ ms}$ to eliminate visual jumping during tab stutter.

> **Completion Criterion**: GeoJSON source promoted with IDs, MMI damage assigned per building, and feature-state $k$ animating collapse without layer rebuilds.

---

## 4. Three.js WebGL Custom Layer & Instanced Physics

Close-up buildings near the camera must break into physical objects with shared depth occlusion:

1. **Shared Context Custom 3D Layer**:
   - Register a custom layer with `renderingMode: "3d"` to share Mapbox's WebGL depth buffer:
     ```javascript
     const mc = mapboxgl.MercatorCoordinate.fromLngLat([origin.lng, origin.lat], 0);
     const s = mc.meterInMercatorCoordinateUnits();
     const toMercator = new THREE.Matrix4()
       .makeTranslation(mc.x, mc.y, mc.z)
       .scale(new THREE.Vector3(s, -s, s));
     ```
   - In `render(gl, matrix)`: multiply projection matrix `camera.projectionMatrix.fromArray(matrix).multiply(toMercator)`. Call `renderer.resetState()` to restore GL bindings.
2. **Oriented Bounding Box (OBB) Derivation**:
   - Find the longest polygon footprint edge to define building yaw angle $\theta_{\text{yaw}}$.
   - Project vertices onto the yaw axis and its normal to extract local dimensions $(L_1, L_2)$ and center offset.
3. **Multi-Block Rigid Body Tipping Physics**:
   - Partition building into 2–4 stacked boxes in a `THREE.Group` hinged on the bottom edge.
   - Integrate angular acceleration: $\theta'' = \frac{1.5 g}{h} \sin \theta$.
   - Enforce safety clamps: angular velocity $\le 2.5\text{ rad/s}$, angular step $\le 0.09\text{ rad/frame}$.
   - Detach upper blocks ballistically when lean exceeds critical threshold; clamp detachment velocity to $\le 18\text{ m/s}$.
4. **Pre-Allocated InstancedMesh Pools**:
   - Pool 30,000 slabs, 1,500 walls, 20,000 rebar segments, and 9,000 rubble rocks.
   - Pre-allocate `instanceColor` attribute for full capacity at initialization (`new Float32Array(capacity * 3).fill(1)`). Lazily sizing to count=0 produces all-black instances.
   - Set `frustumCulled = false` on all custom layer meshes to bypass Three.js camera culling.
   - Invoke `map.triggerRepaint()` every frame objects move.
5. **Event-Driven Dust Particle Plumes**:
   - Do NOT emit constant ambient dust haze. Emit dust puffs strictly on discrete impact events (floor drops, block landings, soft-storey ground-floor jets).
   - Draw dust in screen space on an overlay canvas: project ground anchor with `map.project()`, scale vertical height by $z \cdot \text{scale} \cdot \sin(\text{pitch})$, sort by screen depth, and fade with age.

> **Completion Criterion**: Three.js custom layer rendering tipping multi-block towers, instanced debris landing as permanent rubble, and event-driven dust plumes.

---

## 5. Cinematic Camera Orchestration & Anti-Pattern Defense

1. **Two-Stage Camera Dive**:
   - Ease from regional overview to zoom 14.6 at $45^\circ$ pitch.
   - Pause until `map.areTilesLoaded()` confirms vector tiles have arrived.
   - Ease into zoom 16.2 at $62^\circ$ pitch over epicentre. Skipping the hold renders an empty city.
2. **CSS DOM Container Shake**:
   - Never jitter the map camera with `easeTo`; camera movement forces continuous tile re-fetching.
   - Shake the map DOM container with dynamic CSS transform:
     $$\text{amp} = \min(28, W \cdot 0.02, \max(6, (M - 4) \cdot 4.2))$$
   - Apply envelope ($0.35$ buildup, $0.65$ decay) with rising frequency chirp $\omega(t) = 7 \to 46\text{ rad/s}$.
3. **Zero-Fork Configuration Budget**:
   - Store baseline operational parameters in `config.default.yaml` (max cells, elevation provider, pool sizes, shake durations).

> **Completion Criterion**: Camera dive and CSS container shake execute smoothly, and all 11 field-tested gotchas pass verification.

---

## The Visual Brief

Before running high-density disaster simulations or scaling instanced object pools:
1. **Interactive HTML Diagnostic Brief**: Generate a self-contained visual brief at `%TEMP%\geospatial-disaster-sim-<timestamp>.html`.
2. **Brief Components**:
   - Web Mercator snapped grid extents overlaid on bounding coordinates.
   - Decoded elevation profile heightmap and sea mask boundaries.
   - Seismic attenuation curves (MMI vs distance) and piecewise fragility distribution.
   - Three.js instanced pool capacity allocation table.

---

## Mandatory Checkpoint Gates

Prevent browser WebGL crashes and runaway particle allocations:
1. **Scenario Initialization Gate**: Before downloading vector tiles or allocating Three.js pools, evaluate tile and memory budgets against `config.default.yaml`.
2. **Execution Gate**: When dispatching automated simulation pipelines, emit an `implementation_plan.md` artifact with `RequestFeedback: true` detailing target epicentre, expected collapse counts, and pool capacities before triggering WebGL draw loops.


---

## Diagnostic Coaching & Evaluation Scorecard

| Evaluation Dimension | Pass Criterion (100%) | Failure Mode / Trap |
| :--- | :--- | :--- |
| **Coordinate Space** | Grid snapped to Web Mercator tile boundaries; cell resolution computed in map metres. | Drawing simulation on a floating screen-space canvas overlay. |
| **Elevation Decoding** | Terrarium or Terrain-RGB decoded to 1D Float32Array; median filter removes sensor spikes. | Unfiltered synthetic elevations or non-georeferenced terrain. |
| **Canvas Source Flags** | `animate: true`, `"raster-resampling": "linear"`, `"raster-fade-duration": 0`. | Missing `animate: true` freezes texture on frame 1; default fade smears fluid. |
| **Feature Scaling** | Dedicated GeoJSON source with `promoteId: "i"` driving feature-state `k` multiplier. | Calling `setFeatureState` directly on vector tiles (silent no-op). |
| **WebGL 3D Context** | `renderingMode: "3d"`, shared depth buffer, `frustumCulled = false`, pre-allocated `instanceColor`. | Debris vanishing when panning, or black instances from count=0 buffer. |
| **Camera Shake** | CSS container transform with buildup/decay envelope and frequency chirp. | Shaking map camera directly, triggering tile re-fetch stutter. |

---

## Anti-Patterns

- **Screen-Space Water Overlays** — Drawing ground fluids onto a separate canvas above the map instead of attaching an offscreen canvas as a native map raster source.
- **Silent Feature-State Vector Calls** — Calling `map.setFeatureState()` directly against Mapbox Streets vector tile sources without copying to a GeoJSON source with `promoteId`.
- **Zero-Count Instance Color Allocation** — Allowing Three.js to lazily allocate `instanceColor` when `mesh.count === 0`, causing all instanced debris pieces to render black.
- **Unchecked Camera Frustum Culling** — Leaving `frustumCulled = true` on Three.js custom layer meshes when using a bare camera injected with Mapbox's projection matrix.
- **Direct Camera Jitter Shaking** — Shaking the map view via rapid camera `easeTo` calls, causing severe tile thrashing and stutter instead of shaking the DOM container.
- **Missing Trigger Repaint Invariant** — Updating Three.js objects in memory without calling `map.triggerRepaint()`, leaving the screen unrefreshed when the map is stationary.
- **Sky Layer Depth Occlusion** — Enabling `map.setSky()` alongside a `renderingMode: "3d"` custom layer, causing the sky to write to the depth buffer and occlude 3D objects.
- **Alpha Channel Palette Quantization** — Quantizing sprite PNGs with palette compression, reducing 256 alpha levels to 24 and creating artificial tile-boundary staircasing.
- **Continuous Ambient Dust Haze** — Spawning continuous ambient dust clouds instead of event-driven bursts tied strictly to structural impact moments.
- **Bypassing Vector Tile Load Holds** — Diving the camera directly to zoom 16 without waiting for `map.areTilesLoaded()`, causing buildings to fail to spawn.
