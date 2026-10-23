# /// script
# dependencies = []
# requires-python = ">=3.10"
# ///
"""Geospatial Disaster Simulation Engine

Slotted domain models and mathematical computational solver for real-map
disaster simulations (tsunamis, floods, earthquakes) with tile-aligned
grids, Mercator coordinate transforms, seismic fragility, 5-mode building
collapse physics, and container shake envelopes.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from typing import Sequence

# Rule 23: Windows UTF-8 stream codec entrypoint invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


# ==============================================================================
# Domain Entities (Rule 12: Slotted & Frozen Dataclass Architecture)
# ==============================================================================

@dataclass(slots=True, frozen=True)
class BoundingBox:
    """Geographic bounding box in decimal degrees [w, s, e, n]."""
    w: float
    s: float
    e: float
    n: float

    def __post_init__(self) -> None:
        if not (-180.0 <= self.w <= 180.0 and -180.0 <= self.e <= 180.0):
            raise ValueError(f"Longitude must be within [-180, 180], got w={self.w}, e={self.e}")
        if not (-90.0 <= self.s <= 90.0 and -90.0 <= self.n <= 90.0):
            raise ValueError(f"Latitude must be within [-90, 90], got s={self.s}, n={self.n}")
        if self.w > self.e:
            raise ValueError(f"West longitude ({self.w}) cannot exceed East longitude ({self.e})")
        if self.s > self.n:
            raise ValueError(f"South latitude ({self.s}) cannot exceed North latitude ({self.n})")


@dataclass(slots=True, frozen=True)
class TileGrid:
    """Snapped Web Mercator tile grid specification."""
    z: int
    x0: int
    y0: int
    nx: int
    ny: int
    width_px: int
    height_px: int
    cell_m: float
    corners: BoundingBox

    def __post_init__(self) -> None:
        if self.z < 0 or self.z > 22:
            raise ValueError(f"Zoom level z={self.z} must be in [0, 22]")
        if self.width_px != self.nx * 256 or self.height_px != self.ny * 256:
            raise ValueError("Dimensions must equal tile count * 256 px")


@dataclass(slots=True, frozen=True)
class FragilityPoint:
    """Piecewise point on a seismic fragility curve (MMI to Collapse Probability)."""
    mmi: float
    collapse_prob: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.mmi <= 12.0):
            raise ValueError(f"MMI must be in [0, 12], got {self.mmi}")
        if not (0.0 <= self.collapse_prob <= 1.0):
            raise ValueError(f"Collapse probability must be in [0, 1], got {self.collapse_prob}")


DEFAULT_FRAGILITY_CURVE: tuple[FragilityPoint, ...] = (
    FragilityPoint(mmi=6.5, collapse_prob=0.0),
    FragilityPoint(mmi=7.0, collapse_prob=0.004),
    FragilityPoint(mmi=8.0, collapse_prob=0.025),
    FragilityPoint(mmi=9.0, collapse_prob=0.08),
    FragilityPoint(mmi=10.0, collapse_prob=0.20),
    FragilityPoint(mmi=11.0, collapse_prob=0.38),
    FragilityPoint(mmi=12.0, collapse_prob=0.55),
)


@dataclass(slots=True, frozen=True)
class EarthquakeHypocenter:
    """Seismic rupture parameters."""
    lng: float
    lat: float
    depth_km: float
    magnitude: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.magnitude <= 10.0):
            raise ValueError(f"Magnitude must be in [0, 10], got {self.magnitude}")
        if self.depth_km <= 0.0:
            raise ValueError(f"Focal depth must be positive, got {self.depth_km}")


@dataclass(slots=True, frozen=True)
class BuildingFootprint:
    """Extracted building vector footprint with geometric and physical properties."""
    id: int
    lng: float
    lat: float
    height_m: float
    min_height_m: float
    ring: tuple[tuple[float, float], ...]
    orientation_angle_rad: float
    length1_m: float
    length2_m: float

    def __post_init__(self) -> None:
        if self.height_m < 0.0:
            raise ValueError(f"Building height cannot be negative, got {self.height_m}")
        if len(self.ring) < 3:
            raise ValueError("Building footprint polygon requires at least 3 vertices")


@dataclass(slots=True, frozen=True)
class DamageAssessment:
    """Seismic vulnerability evaluation result for a building."""
    building_id: int
    mmi: float
    collapse_prob: float
    damage_prob: float
    category: int  # 0 = intact, 1 = damaged, 2 = collapsed
    mode: int      # 1=floor-by-floor, 2=soft-storey, 3=crushed-top, 4=sideways, 5=pancake
    start_delay_s: float


@dataclass(slots=True, frozen=True)
class DebrisParticle:
    """Instanced debris fragment simulation state."""
    index: int
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    size: float
    spin: float
    rgb: tuple[float, float, float]
    landed: bool


@dataclass(slots=True, frozen=True)
class DustParticle:
    """Screen-space projected dust plume particle."""
    lng: float
    lat: float
    x_m: float
    y_m: float
    z_m: float
    vx_mps: float
    vy_mps: float
    vz_mps: float
    size: float
    grow: float
    life_s: float
    alpha: float


@dataclass(slots=True, frozen=True)
class ShakeFrame:
    """CSS transform frame parameters for container shake."""
    x_px: float
    y_px: float
    rotate_deg: float
    scale: float
    omega_radps: float
    envelope: float


# ==============================================================================
# Web Mercator Coordinate Projection & Tile Snapping
# ==============================================================================

def lon2x(lon: float, z: int) -> float:
    """Convert longitude in degrees to Web Mercator tile x coordinate at zoom z."""
    return (lon + 180.0) / 360.0 * (2.0 ** z)


def lat2y(lat: float, z: int) -> float:
    """Convert latitude in degrees to Web Mercator tile y coordinate at zoom z."""
    rad = lat * math.pi / 180.0
    return (1.0 - math.log(math.tan(rad) + 1.0 / math.cos(rad)) / math.pi) / 2.0 * (2.0 ** z)


def x2lon(x: float, z: int) -> float:
    """Convert Web Mercator tile x coordinate at zoom z to longitude in degrees."""
    return x / (2.0 ** z) * 360.0 - 180.0


def y2lat(y: float, z: int) -> float:
    """Convert Web Mercator tile y coordinate at zoom z to latitude in degrees."""
    n = math.pi - 2.0 * math.pi * y / (2.0 ** z)
    return 180.0 / math.pi * math.atan(0.5 * (math.exp(n) - math.exp(-n)))


def choose_zoom(bbox: BoundingBox, max_width_px: int = 780, max_cells: int = 620000) -> int:
    """Select the highest zoom level where the snapped bounding box fits operational budgets."""
    for z in range(15, 7, -1):
        pw = (lon2x(bbox.e, z) - lon2x(bbox.w, z)) * 256.0
        ph = (lat2y(bbox.s, z) - lat2y(bbox.n, z)) * 256.0
        if pw <= max_width_px and pw * ph <= max_cells:
            return z
    return 8


def grid_for(bbox: BoundingBox, max_width_px: int = 780, max_cells: int = 620000) -> TileGrid:
    """Calculate the tile-snapped grid specification and geographic corners for a bounding box."""
    z = choose_zoom(bbox, max_width_px=max_width_px, max_cells=max_cells)
    x0 = math.floor(lon2x(bbox.w, z))
    x1 = math.floor(lon2x(bbox.e, z))
    y0 = math.floor(lat2y(bbox.n, z))
    y1 = math.floor(lat2y(bbox.s, z))
    nx = x1 - x0 + 1
    ny = y1 - y0 + 1
    lat_mid = (bbox.n + bbox.s) / 2.0

    # Metres per cell along equator scaled by cos(lat)
    cell_m = 156543.03392 * math.cos(lat_mid * math.pi / 180.0) / (2.0 ** z)

    corners = BoundingBox(
        w=x2lon(x0, z),
        e=x2lon(x1 + 1, z),
        s=y2lat(y1 + 1, z),
        n=y2lat(y0, z),
    )

    return TileGrid(
        z=z,
        x0=x0,
        y0=y0,
        nx=nx,
        ny=ny,
        width_px=nx * 256,
        height_px=ny * 256,
        cell_m=cell_m,
        corners=corners,
    )


# ==============================================================================
# Elevation Decoding & Spike Filtering
# ==============================================================================

def decode_terrarium_pixel(r: int, g: int, b: int) -> float:
    """Decode AWS Mapzen Terrarium PNG RGB pixel to elevation in metres.
    
    Formula: height_m = R * 256 + G + B / 256 - 32768
    """
    return r * 256.0 + g + b / 256.0 - 32768.0


def decode_terrain_rgb_pixel(r: int, g: int, b: int) -> float:
    """Decode Mapbox Terrain-RGB pixel to elevation in metres.
    
    Formula: height_m = -10000 + (R * 65536 + G * 256 + B) * 0.1
    """
    return -10000.0 + (r * 65536.0 + g * 256.0 + b) * 0.1


def median_filter_1d(elev: list[float], width: int, height: int, threshold_m: float = 8.0) -> list[float]:
    """Run a 3x3 median pass to filter single-pixel sensor spikes in elevation arrays."""
    filtered = list(elev)
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            idx = y * width + x
            val = elev[idx]
            neighbors = [
                elev[(y + dy) * width + (x + dx)]
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
            ]
            neighbors.sort()
            median = neighbors[4]
            if abs(val - median) >= threshold_m:
                filtered[idx] = median
    return filtered


# ==============================================================================
# Seaward Camera Orientation Calculus
# ==============================================================================

def calculate_seaward_bearing(
    grid: TileGrid,
    sea_mask: Sequence[bool],
    center_lng: float,
    center_lat: float,
    search_radius_m: float = 2500.0,
    inland_offset_m: float = 900.0,
) -> tuple[float, float, float]:
    """Calculate the shore camera position and seaward bearing facing the ocean.
    
    Returns:
        (cam_lng, cam_lat, bearing_deg)
    """
    w, h, z, x0, y0 = grid.width_px, grid.height_px, grid.z, grid.x0, grid.y0
    best_idx = -1
    best_dist = float("inf")

    # 1. Find nearest coastline cell to map center
    for i in range(w * h):
        if not sea_mask[i]:
            continue
        x = i % w
        y = i // w
        is_coast = (
            (x > 0 and not sea_mask[i - 1]) or
            (x < w - 1 and not sea_mask[i + 1]) or
            (y > 0 and not sea_mask[i - w]) or
            (y < h - 1 and not sea_mask[i + w])
        )
        if not is_coast:
            continue
        lng = x2lon(x0 + (x + 0.5) / 256.0, z)
        lat = y2lat(y0 + (y + 0.5) / 256.0, z)
        d = (lng - center_lng) ** 2 + (lat - center_lat) ** 2
        if d < best_dist:
            best_dist = d
            best_idx = i

    if best_idx == -1:
        return (center_lng, center_lat, 0.0)

    sx = best_idx % w
    sy = best_idx // w

    # 2. Local seaward direction: average vector offset to sea cells within search radius
    r = max(6, round(search_radius_m / grid.cell_m))
    vx, vy = 0.0, 0.0
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            nx, ny = sx + dx, sy + dy
            if nx < 0 or ny < 0 or nx >= w or ny >= h or not sea_mask[ny * w + nx]:
                continue
            length = math.hypot(dx, dy)
            if length < 1.0 or length > r:
                continue
            vx += dx / length
            vy += dy / length

    length = math.hypot(vx, vy) or 1.0
    east = vx / length
    north = -vy / length  # Grid y grows southward, hence negate vy

    shore_lng = x2lon(x0 + (sx + 0.5) / 256.0, z)
    shore_lat = y2lat(y0 + (sy + 0.5) / 256.0, z)
    m_lng = 111320.0 * math.cos(shore_lat * math.pi / 180.0)
    m_lat = 110574.0

    cam_lng = shore_lng - east * inland_offset_m / m_lng
    cam_lat = shore_lat - north * inland_offset_m / m_lat
    bearing = math.atan2(east, north) * 180.0 / math.pi

    return (cam_lng, cam_lat, bearing)


# ==============================================================================
# Seismic Attenuation & Fragility Curves
# ==============================================================================

def mmi_at(magnitude: float, r_km: float, depth_km: float = 10.0) -> float:
    """Calculate Modified Mercalli Intensity (MMI) from magnitude and epicentral distance.
    
    Formula:
        R = sqrt(r_km^2 + depth_km^2)
        MMI = 1.5 * M - 3.0 * log10(R) - 0.0018 * R + 1.6
    Bounded between 0.0 and 12.0.
    """
    hypocentral_r = math.sqrt(r_km * r_km + depth_km * depth_km)
    v = 1.5 * magnitude - 3.0 * math.log10(hypocentral_r) - 0.0018 * hypocentral_r + 1.6
    return max(0.0, min(12.0, v))


def collapse_probability(
    mmi: float,
    fragility: Sequence[FragilityPoint] = DEFAULT_FRAGILITY_CURVE,
) -> float:
    """Interpolate collapse probability from MMI using a piecewise linear fragility curve."""
    if mmi <= fragility[0].mmi:
        return 0.0
    for i in range(1, len(fragility)):
        if mmi <= fragility[i].mmi:
            p0, p1 = fragility[i - 1], fragility[i]
            frac = (mmi - p0.mmi) / (p1.mmi - p0.mmi)
            return p0.collapse_prob + frac * (p1.collapse_prob - p0.collapse_prob)
    return fragility[-1].collapse_prob


def evaluate_building_damage(
    building: BuildingFootprint,
    quake: EarthquakeHypocenter,
    quality_multiplier: float = 1.0,
    random_seed_val: float = 0.5,
) -> DamageAssessment:
    """Evaluate seismic damage category, collapse probability, and collapse mode for a building."""
    kx = 111320.0 * math.cos(quake.lat * math.pi / 180.0)
    ky = 110574.0
    r_km = math.hypot((building.lng - quake.lng) * kx, (building.lat - quake.lat) * ky) / 1000.0

    mmi = mmi_at(quake.magnitude, r_km, depth_km=quake.depth_km)

    # Height factor: mid-rise buildings fare worst, tall engineered ones fare better
    h = building.height_m
    if h < 5.0:
        hf = 0.7
    elif h < 35.0:
        hf = 1.15
    elif h < 70.0:
        hf = 0.8
    else:
        hf = 0.45

    base_p = collapse_probability(mmi)
    p_collapse = min(0.9, base_p * quality_multiplier * hf)
    p_damage = min(0.6, p_collapse * 2.5 + 0.004) if mmi >= 6.0 else 0.0

    if random_seed_val < p_collapse:
        cat = 2  # Collapsed
    elif random_seed_val < p_collapse + p_damage:
        cat = 1  # Damaged
    else:
        cat = 0  # Intact

    # Collapse mode selection (1=floor-by-floor, 2=soft-storey, 3=crushed-top, 4=sideways, 5=pancake)
    mode = 1 + int(random_seed_val * 5) % 5
    start_delay_s = 0.8 + (random_seed_val * 2.8)

    return DamageAssessment(
        building_id=building.id,
        mmi=mmi,
        collapse_prob=p_collapse,
        damage_prob=p_damage,
        category=cat,
        mode=mode,
        start_delay_s=start_delay_s,
    )


# ==============================================================================
# 5 Building Collapse Mode Multipliers
# ==============================================================================

def collapse_k(
    mode: int,
    u: float,
    k0: float = 1.0,
    kf: float = 0.15,
    height_m: float = 30.0,
    num_steps: int = 4,
) -> float:
    """Calculate the height multiplier k(u) for a building collapse progress u in [0, 1]."""
    u = max(0.0, min(1.0, u))
    span = k0 - kf

    if mode == 1:  # Floor-by-floor: staircase of fast drops and pauses
        s = u * num_steps
        i = min(num_steps - 1, math.floor(s))
        f = s - i
        f_curv = (f * f / 0.45 * 1.1) if f < 0.45 else (0.55 + (f - 0.45) * 0.45 / 0.55)
        return k0 - span * min(1.0, (i + min(1.0, f_curv)) / num_steps)

    elif mode == 2:  # Soft-storey: ground floor drops, pauses, then collapses
        sd = min(span * 0.5, 3.2 / max(1.0, height_m))
        if u < 0.12:
            return k0 - sd * ((u / 0.12) ** 2)
        if u < 0.5:
            return k0 - sd
        v = (u - 0.5) / 0.5
        return k0 - sd - (span - sd) * (v * v)

    elif mode == 3:  # Crushed top: upper part fails first
        pt = span * 0.45
        if u < 0.3:
            return k0 - pt * ((u / 0.3) ** 2)
        if u < 0.55:
            return k0 - pt
        v = (u - 0.55) / 0.45
        return k0 - pt - (span - pt) * (v * v)

    elif mode == 4:  # Sideways: steady, slightly accelerating
        return k0 - span * (u ** 1.6)

    else:  # Mode 5 (Default): Pancake accelerating free fall
        return k0 - span * (u * u)


# ==============================================================================
# Geometric Oriented Bounding Box (OBB) Derivation
# ==============================================================================

def compute_oriented_bounding_box(
    ring: Sequence[tuple[float, float]],
    origin_lng: float,
    origin_lat: float,
) -> tuple[float, float, float, float, float]:
    """Compute local center (x, y), yaw angle, and side lengths (L1, L2) in metres from footprint.
    
    Returns:
        (center_x_m, center_y_m, yaw_rad, length1_m, length2_m)
    """
    kx = 111320.0 * math.cos(origin_lat * math.pi / 180.0)
    ky = 110574.0

    loc = [((lng - origin_lng) * kx, (lat - origin_lat) * ky) for lng, lat in ring]

    # Find longest edge to establish orientation angle
    best_len_sq = 0.0
    ang = 0.0
    for i in range(1, len(loc)):
        ex = loc[i][0] - loc[i - 1][0]
        ey = loc[i][1] - loc[i - 1][1]
        dist_sq = ex * ex + ey * ey
        if dist_sq > best_len_sq:
            best_len_sq = dist_sq
            ang = math.atan2(ey, ex)

    # Project vertices onto axis and normal
    ca, sa = math.cos(ang), math.sin(ang)
    u0, u1 = float("inf"), float("-inf")
    v0, v1 = float("inf"), float("-inf")
    for x, y in loc:
        u = x * ca + y * sa
        v = -x * sa + y * ca
        u0 = min(u0, u)
        u1 = max(u1, u)
        v0 = min(v0, v)
        v1 = max(v1, v)

    cu = (u0 + u1) / 2.0
    cv = (v0 + v1) / 2.0

    center_x = cu * ca - cv * sa
    center_y = cu * sa + cv * ca
    l1 = max(2.0, u1 - u0)
    l2 = max(2.0, v1 - v0)

    return (center_x, center_y, ang, l1, l2)


# ==============================================================================
# Rigid Body Kinematics & Container Shake
# ==============================================================================

def simulate_rigid_body_tip_step(
    height_m: float,
    current_th_rad: float,
    current_w_radps: float,
    dt_s: float,
    g: float = 9.8,
) -> tuple[float, float]:
    """Execute one simulation step for a tipping rigid building block.
    
    Angular acceleration:
        theta'' = (1.5 * g / h) * sin(theta)
    Clamped to prevent unphysical numerical explosions during framerate hiccups.
    
    Returns:
        (new_theta_rad, new_omega_radps)
    """
    dt_clamped = max(0.008, min(0.04, dt_s))
    ang_accel = 1.5 * g / max(1.0, height_m) * math.sin(current_th_rad)
    w_new = min(2.5, current_w_radps + ang_accel * dt_clamped)
    th_step = min(0.09, w_new * dt_clamped)
    th_new = current_th_rad + th_step
    return (th_new, w_new)


def compute_container_shake_frame(
    elapsed_ms: float,
    total_duration_ms: float,
    magnitude: float,
    container_w: float = 1920.0,
    container_h: float = 1080.0,
    phase: float = 0.0,
    direction_rad: float = 0.785,
) -> ShakeFrame:
    """Calculate CSS container shake transform parameters with buildup, decay, and frequency chirp."""
    k = max(0.0, min(1.0, elapsed_ms / max(1.0, total_duration_ms)))
    amp = min(28.0, max(6.0, (magnitude - 4.0) * 4.2))

    # Envelope and frequency chirp
    if k < 0.35:
        u = k / 0.35
        env = 0.15 + 0.85 * (u * u) * (3.0 - 2.0 * u)
        omega = 7.0 + 39.0 * (u * u)
    else:
        v = (k - 0.35) / 0.65
        env = (1.0 - v) ** 1.4
        omega = 46.0 - 18.0 * v

    a = amp * env
    osc = math.sin(phase) * 0.78
    x = math.cos(direction_rad) * osc * a
    y = math.sin(direction_rad) * osc * a * 0.7
    rot = osc * a * 0.012
    scale = 1.0 + 2.4 * amp / min(container_w, container_h) * env

    return ShakeFrame(
        x_px=x,
        y_px=y,
        rotate_deg=rot,
        scale=scale,
        omega_radps=omega,
        envelope=env,
    )


# ==============================================================================
# CLI Entrypoint (Rule 10: Headless CLI Introspection Seams)
# ==============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(description="Geospatial Disaster Simulation Engine CLI")
    parser.add_argument("--summary", action="store_true", help="Print simulation capabilities summary")
    parser.add_argument("--demo-quake", action="store_true", help="Run sample earthquake damage evaluation")
    parser.add_argument("--json", action="store_true", help="Emit output as JSON")
    args = parser.parse_args()

    if args.demo_quake or args.summary:
        bbox = BoundingBox(w=30.65, s=46.40, e=30.80, n=46.55)
        grid = grid_for(bbox)
        quake = EarthquakeHypocenter(lng=30.73, lat=46.48, depth_km=10.0, magnitude=7.2)

        test_footprint = BuildingFootprint(
            id=101,
            lng=30.74,
            lat=46.49,
            height_m=32.0,
            min_height_m=0.0,
            ring=((30.739, 46.489), (30.741, 46.489), (30.741, 46.491), (30.739, 46.491)),
            orientation_angle_rad=0.0,
            length1_m=20.0,
            length2_m=15.0,
        )

        damage = evaluate_building_damage(test_footprint, quake, quality_multiplier=1.0)
        obb = compute_oriented_bounding_box(test_footprint.ring, quake.lng, quake.lat)

        data = {
            "grid": {
                "zoom": grid.z,
                "tiles_x": grid.nx,
                "tiles_y": grid.ny,
                "width_px": grid.width_px,
                "height_px": grid.height_px,
                "cell_resolution_m": round(grid.cell_m, 2),
            },
            "earthquake": {
                "magnitude": quake.magnitude,
                "depth_km": quake.depth_km,
                "building_id": damage.building_id,
                "intensity_mmi": round(damage.mmi, 2),
                "collapse_prob": round(damage.collapse_prob, 4),
                "damage_prob": round(damage.damage_prob, 4),
                "damage_category": damage.category,
                "collapse_mode": damage.mode,
            },
            "obb": {
                "center_x_m": round(obb[0], 2),
                "center_y_m": round(obb[1], 2),
                "yaw_deg": round(math.degrees(obb[2]), 2),
                "length1_m": round(obb[3], 2),
                "length2_m": round(obb[4], 2),
            },
        }

        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print("==================================================")
            print(" GEOSPATIAL DISASTER SIMULATION ENGINE SUMMARY")
            print("==================================================")
            print(f"Grid: Zoom {grid.z} ({grid.width_px}x{grid.height_px} px, {grid.cell_m:.2f} m/cell)")
            print(f"Quake: M{quake.magnitude} (Depth: {quake.depth_km} km)")
            print(f"Building {damage.building_id}: MMI {damage.mmi:.2f}, Category={damage.category}, Mode={damage.mode}")
            print(f"Oriented Box: L1={obb[3]:.1f}m, L2={obb[4]:.1f}m, Yaw={math.degrees(obb[2]):.1f}°")
            print("Status: OK (Slotted Engine Active)")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
