# Quick Reference Card: Geospatial Disaster Simulation

```
┌─────────────────────────────────────────────────────────────────────────┐
│ SKILL: geospatial-disaster-simulation                                   │
│ DOMAIN: Geospatial Fluid & 3D Structural Simulation                     │
│ PARADIGM: Dual-World Architecture (Ground Draping + Shared 3D Context)  │
│ ATTRIBUTION: Alex Oliinyk (HazardSim / freeCodeCamp)                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5-Stage Pipeline Progression

| Stage | Focus Area | Key Technical Deliverables | Verification Gate |
| :--- | :--- | :--- | :--- |
| **1. Grid & Elevation** | Web Mercator Tile Grid | Mercator projection, budgeted zoom, Terrarium / Terrain-RGB decoding, median spike filter. | $1\text{D}$ Float32Array elevation grid aligned $1$-to-$1$ with tiles; no resampling. |
| **2. Ground Fluid** | Raster Canvas Draping | Offscreen canvas source (`animate: true`), `source-atop` + `destination-in` compositing, seaward camera. | Floodwater follows terrain contour with zero perspective drift when pitching. |
| **3. Footprint Scaling** | Feature-State Collapse | GeoJSON promotion (`promoteId: "i"`), MMI attenuation, fragility curves, 5 collapse modes. | Extrusions shrink via feature-state multiplier $k$; no layer rebuilding. |
| **4. 3D WebGL Context** | Three.js Custom Layer | `renderingMode: "3d"`, Mercator transform matrix, OBB box, multi-block tip, instanced pools. | Falling towers, ballistic debris, and rubble share Mapbox depth buffer. |
| **5. Cinematic Camera** | Camera Choreography | 2-stage hold camera dive, CSS container shake envelope with frequency chirp, gotcha defenses. | Shaking container avoids tile thrashing; vector tiles loaded prior to collapse. |

---

## The Three Foundational Pillars

### 1. Dual-World Coordinate Separation
- **Ground Tier**: Ground fluids must be rendered into an offscreen canvas registered as a native map raster source with `animate: true`. The map engine handles rotation, tilt, and 3D terrain mesh draping for free.
- **Height Tier**: Height objects must live in a Three.js custom layer configured with `renderingMode: "3d"` inside Mapbox's WebGL context, sharing the depth buffer so 3D meshes correctly occlude extruded buildings.

### 2. Feature-State PromoteId Scaling
- Vector tile buildings from Mapbox Streets lack native feature IDs; calling `map.setFeatureState()` against vector sources fails silently with no error.
- Extract building footprints into a dedicated GeoJSON source configured with `promoteId: "i"`. Modulate the height multiplier $k$ per frame without touching layer geometries.

### 3. Container-Level Dynamic Shake
- Never shake the map camera via `map.easeTo()`; camera position changes trigger continuous vector and raster tile re-fetching, destroying frame rates.
- Apply dynamic CSS transforms (`translate`, `rotate`, `scale`) to the map container element with a $0.35$ buildup / $0.65$ decay envelope and a rising frequency chirp $\omega(t) = 7 \to 46\text{ rad/s}$.

---

## Key Mathematical & Physical Formulas

```
1. Terrarium Elevation:   height_m = R * 256 + G + B / 256 - 32768
2. Terrain-RGB Elevation: height_m = -10000 + (R * 65536 + G * 256 + B) * 0.1
3. Seismic Attenuation:   R = sqrt(r_km^2 + depth_km^2)
                          MMI = 1.5 * M - 3.0 * log10(R) - 0.0018 * R + 1.6
4. Rigid Body Lean:       theta'' = (1.5 * g / h) * sin(theta)  [clamp w <= 2.5 rad/s]
5. Mercator Transform:    toMercator = Matrix4().makeTranslation(mc.x, mc.y, mc.z)
                                                .scale(Vector3(s, -s, s))
```

---

## Mandatory Invariants Checklist

- [ ] Canvas source is initialized with `animate: true`, `"raster-resampling": "linear"`, and `"raster-fade-duration": 0`.
- [ ] Offscreen building GeoJSON source explicitly declares `promoteId: "i"` before feature-state mutations.
- [ ] Three.js custom layer is configured with `renderingMode: "3d"` and autoClear disabled.
- [ ] All InstancedMesh pools pre-allocate `instanceColor` attribute for full capacity before setting counts.
- [ ] All custom layer meshes have `frustumCulled = false` set explicitly.
- [ ] `map.triggerRepaint()` is called at the end of every animation frame where objects move.
- [ ] Map camera dive holds at zoom 14.6 until `map.areTilesLoaded()` returns true before diving to zoom 16.2.
- [ ] Map sky layer (`map.setSky()`) is omitted or disabled when 3D custom layers are active.
- [ ] Seismic camera shaking is applied to the DOM container element, not the map camera camera matrix.
