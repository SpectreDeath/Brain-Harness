# Knowledge Item Summary: Geospatial Disaster Simulation on Real Maps

**Item ID**: `ki_oliinyk_geospatial_disaster_simulation`  
**Author**: Alex Oliinyk ([HazardSim](https://hazardsim.com/) / freeCodeCamp.org)  
**Synthesized By**: Brain Harness Deep-Skill Forge  
**Created**: October 2026  
**Primary Discipline**: Geospatial Fluid & 3D Structural Simulation  

---

## 1. Epistemic Introspection & Foundational Mental Models

Building simulations of real-world physical catastrophes (tsunamis, dam breaches, earthquake structural collapses) on interactive web maps inevitably confronts the **"Abstraction Problem"**: naive implementations treat the map as a background 2D image and draw dynamic effects on an overlaid `<canvas>` element in screen space.

This produces the **"Sticker Problem"**:
- Effects have artificial rectangular boundaries that clip against the viewport.
- Fluid surfaces float above ground rather than contouring around hills, valleys, and shorelines.
- When the user rotates or pitches the map, the simulation desynchronizes from the ground layer.
- 3D buildings cannot interact with fluid or debris because there is no shared depth buffer.

### The Core Paradigm Shift: Dual-World Coordinate Separation
The fundamental resolution is to bifurcate the simulation into two coordinated physical tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        THE DUAL-TIER SEAM                              │
├───────────────────────────────────┬────────────────────────────────────┤
│ 1. Ground Tier (Surface Fluids)   │ 2. Height Tier (3D Structures)     │
│ - Tiled Web Mercator Grid         │ - Vector Building Footprints       │
│ - Real Elevation Decoded (PNGs)   │ - Feature-State Scaling (GeoJSON)  │
│ - Native Canvas Raster Source     │ - Shared WebGL 3D Context (Three)  │
│ - Draped automatically by Mapbox  │ - Shared Depth Buffer Occlusion    │
└───────────────────────────────────┴────────────────────────────────────┘
```

By dividing the world into **things on the ground** and **things with height**, each layer is delegated to the graphics technology uniquely optimized for it:
- The **Map Engine (Mapbox GL JS / MapLibre GL)** is unparalleled at rendering 10,000+ static 3D building extrusions and draping textures over terrain meshes.
- **Three.js** inside the map's WebGL context is optimal for 10–50 moving, breaking, tipping rigid bodies with instanced physics.
- The seam between them is the **Mercator-to-metric coordinate transform** and the **`promoteId` feature-state multiplier**.

---

## 2. Mathematical & Algorithmic Formulations

### A. Web Mercator Grid Snapping & Resolution
To ingest tiled elevation datasets without interpolation artifacts, the simulation grid is snapped to whole tiles:
$$\text{cellM} = \frac{156543.03392 \cdot \cos(\text{lat})}{2^z}$$
Zoom level $z$ is dynamically budgeted such that grid width $\le 780\text{ px}$ and cell count $\le 620,000\text{ cells}$.

### B. Elevation Tile Decoding Formulas
1. **AWS Mapzen Terrarium PNGs**:
   $$\text{height}_m = R \cdot 256 + G + \frac{B}{256} - 32768$$
2. **Mapbox Terrain-RGB**:
   $$\text{height}_m = -10000 + (R \cdot 65536 + G \cdot 256 + B) \cdot 0.1$$

Single-pixel sensor spikes are scrubbed via a $3 \times 3$ median filter where values differing from neighbors by $> 8\text{ m}$ are replaced by the median.

### C. Seismic Attenuation & Fragility
Shaking intensity at building distance $r_{\text{km}}$ from an earthquake of magnitude $M$ with hypocentral depth $d_{\text{km}}$:
$$R = \sqrt{r_{\text{km}}^2 + d_{\text{km}}^2}$$
$$\text{MMI} = 1.5 M - 3.0 \log_{10}(R) - 0.0018 R + 1.6$$
Collapse probability is evaluated via piecewise linear interpolation along the standard fragility curve:
`[[6.5, 0], [7, 0.004], [8, 0.025], [9, 0.08], [10, 0.20], [11, 0.38], [12, 0.55]]`, scaled by structural quality factor $q$ and height vulnerability $h_f$.

### D. Rigid Body Falling Dynamics
A tipping building behaves as a rigid body hinged along its base edge:
$$\theta'' = \frac{1.5 g}{h} \sin \theta$$
Angular velocity is clamped to $\le 2.5\text{ rad/s}$ and angular step per frame to $\le 0.09\text{ rad}$. When upper blocks detach ballistically, detachment velocity is clamped to $\le 18\text{ m/s}$ to prevent numerical explosion during framerate hiccups.

---

## 3. The 11 Field-Tested Gotchas Post-Mortem

| # | Gotcha / Failure Mode | Root Cause | Verified Antidote |
| :---: | :--- | :--- | :--- |
| **1** | **The Sticker Problem** | Drawing water on a screen-space canvas overlay. | Register offscreen canvas as a native map raster source with `animate: true`. |
| **2** | **Inverted Layer Placement** | `map.addLayer(layer, "flood")` places 3D under opaque ground fluid. | Query `map.getStyle().layers` and insert before the first `symbol` layer. |
| **3** | **24 Levels of Transparency** | `PIL.Image.quantize()` compresses alpha channels along with RGB. | Never palette-quantize alpha on sprite sheets; inspect alpha with histograms. |
| **4** | **CDN Cache Invalidation** | CDNs caching binary WebM assets ignoring `?v=2` query strings. | Rename binary assets directly (`flood2.webm`) on deploy. |
| **5** | **Headless Screenshot Lies** | Software GL delays frame capture; satellite tiles take seconds to arrive. | Poll `map.areTilesLoaded()` before capturing frames or reading pixels. |
| **6** | **Silent Feature State Failure** | Vector tiles have no feature IDs; `setFeatureState` silently fails. | Copy buildings to GeoJSON with `promoteId: "i"` so `id` reaches features. |
| **7** | **All-Black Instanced Meshes** | Three.js lazily sizes `instanceColor` to `count=0` at initialization. | Pre-allocate `instanceColor` for the full pool capacity before first use. |
| **8** | **Debris Frustum Vanishing** | Three.js frustum-culls against a bare camera lacking map view bounds. | Explicitly set `frustumCulled = false` on all custom layer meshes. |
| **9** | **Scene Updates Without Screen** | Mapbox only repaints when it detects its own internal mutations. | Invoke `map.triggerRepaint()` at the end of every animation frame. |
| **10** | **Sky Layer Depth Occlusion** | `map.setSky()` writes to the depth buffer, occluding subsequent 3D draws. | Never enable Mapbox sky layers when rendering 3D custom layers. |
| **11** | **Background Tab Idle Stall** | Preloading models on `map.on("idle")` hangs indefinitely in background tabs. | Preload 3D assets immediately on user scenario selection intent. |

---

## 4. Architectural Rules of Thumb for Simulation Agents

1. **Draw in World Coordinates**: If an object exists in physical space, its coordinates must be $(\text{lng}, \text{lat}, z_{\text{elev}})$. Draping on ground eliminates all camera projection math.
2. **Never Rebuild Layers in Animation Loops**: Animate extrusions via `feature-state` height multipliers. Re-uploading GeoJSON features 60 times a second creates garbage-collection stutter.
3. **Pre-Allocate Fixed Pool Capacities**: Debris pieces must be pulled from fixed-capacity `InstancedMesh` pools. Pieces that land simply cease updating and remain as permanent rubble at zero extra draw-call cost.
4. **Shake the Container, Not the Camera**: Never use `easeTo` to jitter camera coordinates. Apply CSS transforms to the map container with buildup/decay envelopes and frequency chirps.
