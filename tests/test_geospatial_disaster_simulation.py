"""Unit and contract tests for the Geospatial Disaster Simulation Engine.

Verifies slotted and frozen dataclass architecture, Web Mercator projection
precision, elevation decoding, seismic attenuation, 5-mode collapse curves,
oriented bounding box geometry, and container shake envelopes.
"""

import math
import sys
from pathlib import Path

import pytest

# Ensure skill scripts path is importable
SKILL_DIR = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "geospatial-disaster-simulation" / "scripts"
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from disaster_sim_engine import (
    BoundingBox,
    TileGrid,
    FragilityPoint,
    EarthquakeHypocenter,
    BuildingFootprint,
    DamageAssessment,
    ShakeFrame,
    lon2x,
    lat2y,
    x2lon,
    y2lat,
    choose_zoom,
    grid_for,
    decode_terrarium_pixel,
    decode_terrain_rgb_pixel,
    median_filter_1d,
    calculate_seaward_bearing,
    mmi_at,
    collapse_probability,
    evaluate_building_damage,
    collapse_k,
    compute_oriented_bounding_box,
    simulate_rigid_body_tip_step,
    compute_container_shake_frame,
)


# ==============================================================================
# 1. Slotted & Frozen Dataclass Immutability (Rule 12 & Rule 43)
# ==============================================================================

def test_frozen_dataclass_immutability():
    """Rule 43: Verify immutability of slotted/frozen dataclasses via direct assignment."""
    bbox = BoundingBox(w=30.0, s=46.0, e=31.0, n=47.0)
    with pytest.raises((AttributeError, TypeError)):
        bbox.w = 32.0  # type: ignore

    quake = EarthquakeHypocenter(lng=30.7, lat=46.4, depth_km=10.0, magnitude=7.0)
    with pytest.raises((AttributeError, TypeError)):
        quake.magnitude = 8.5  # type: ignore

    frag = FragilityPoint(mmi=8.0, collapse_prob=0.025)
    with pytest.raises((AttributeError, TypeError)):
        frag.collapse_prob = 0.5  # type: ignore


def test_bounding_box_validation():
    """Verify BoundingBox enforces geographic bounds and ordering invariants."""
    with pytest.raises(ValueError, match="Longitude must be within"):
        BoundingBox(w=-190.0, s=10.0, e=20.0, n=30.0)

    with pytest.raises(ValueError, match="Latitude must be within"):
        BoundingBox(w=10.0, s=-95.0, e=20.0, n=30.0)

    with pytest.raises(ValueError, match="cannot exceed East"):
        BoundingBox(w=25.0, s=10.0, e=20.0, n=30.0)

    with pytest.raises(ValueError, match="cannot exceed North"):
        BoundingBox(w=10.0, s=35.0, e=20.0, n=30.0)


# ==============================================================================
# 2. Web Mercator Coordinate Projections
# ==============================================================================

def test_web_mercator_round_trip():
    """Verify Web Mercator projection and unprojection round-trip precision."""
    test_coords = [
        (0.0, 0.0),        # Null Island
        (30.73, 46.48),    # Odesa
        (-74.006, 40.712), # New York
        (139.69, 35.68),   # Tokyo
        (-0.12, 51.50),    # London
    ]
    zoom = 12
    for lon, lat in test_coords:
        x = lon2x(lon, zoom)
        y = lat2y(lat, zoom)
        un_lon = x2lon(x, zoom)
        un_lat = y2lat(y, zoom)
        assert pytest.approx(lon, abs=1e-5) == un_lon
        assert pytest.approx(lat, abs=1e-5) == un_lat


def test_zoom_selection_and_grid_snapping():
    """Verify choose_zoom and grid_for adhere to max width and pixel budgets."""
    bbox = BoundingBox(w=30.65, s=46.40, e=30.80, n=46.55)
    grid = grid_for(bbox, max_width_px=780, max_cells=620000)

    assert 8 <= grid.z <= 15
    assert grid.width_px <= 780
    assert grid.width_px * grid.height_px <= 620000
    assert grid.cell_m > 0.0

    # Corners must encompass original bbox
    assert grid.corners.w <= bbox.w
    assert grid.corners.e >= bbox.e
    assert grid.corners.s <= bbox.s
    assert grid.corners.n >= bbox.n


# ==============================================================================
# 3. Elevation Tile Decoding & Spike Filtering
# ==============================================================================

def test_terrarium_elevation_decoding():
    """Verify AWS Terrarium PNG pixel decoding formula."""
    # Sea level (0m) corresponds to R=128, G=0, B=0 -> 128*256 - 32768 = 0
    assert decode_terrarium_pixel(128, 0, 0) == 0.0

    # Positive elevation: 128*256 + 100 - 32768 = 100.0m
    assert decode_terrarium_pixel(128, 100, 0) == 100.0

    # Fractional metres: B=128 -> +0.5m
    assert decode_terrarium_pixel(128, 100, 128) == 100.5


def test_terrain_rgb_elevation_decoding():
    """Verify Mapbox Terrain-RGB pixel decoding formula."""
    # Sea level (0m): -10000 + (val) * 0.1 = 0 => val = 100000 => 1*65536 + 134*256 + 160
    r, g, b = 1, 134, 160
    assert pytest.approx(decode_terrain_rgb_pixel(r, g, b), abs=0.1) == 0.0

    # 500m elevation: val = 105000
    val = 105000
    r = val // 65536
    rem = val % 65536
    g = rem // 256
    b = rem % 256
    assert pytest.approx(decode_terrain_rgb_pixel(r, g, b), abs=0.1) == 500.0


def test_median_filter_1d_spike_removal():
    """Verify 3x3 median filter suppresses single-pixel elevation spikes."""
    w, h = 5, 5
    elev = [10.0] * (w * h)
    # Inject a 50m sensor artifact at center (2, 2)
    spike_idx = 2 * w + 2
    elev[spike_idx] = 60.0

    filtered = median_filter_1d(elev, w, h, threshold_m=8.0)
    assert filtered[spike_idx] == 10.0
    assert filtered[0] == 10.0


# ==============================================================================
# 4. Coastal Camera Seaward Bearing Calculus
# ==============================================================================

def test_seaward_bearing_calculus():
    """Verify seaward camera bearing calculation faces open sea."""
    bbox = BoundingBox(w=30.70, s=46.45, e=30.76, n=46.51)
    grid = grid_for(bbox)
    w, h = grid.width_px, grid.height_px

    # Create artificial coastline: West half is land, East half is sea
    sea_mask = [False] * (w * h)
    for y in range(h):
        for x in range(w // 2, w):
            sea_mask[y * w + x] = True

    center_lng = (bbox.w + bbox.e) / 2.0
    center_lat = (bbox.s + bbox.n) / 2.0
    cam_lng, cam_lat, bearing = calculate_seaward_bearing(
        grid, sea_mask, center_lng, center_lat, search_radius_m=1000.0, inland_offset_m=500.0
    )

    # Ocean is East, so seaward bearing should be approximately 90 degrees East
    assert pytest.approx(bearing, abs=15.0) == 90.0
    # Camera should be placed inland (West of shore)
    assert cam_lng < center_lng


# ==============================================================================
# 5. Seismic Attenuation & Fragility Curves
# ==============================================================================

def test_mmi_attenuation():
    """Verify MMI decreases monotonically with distance from hypocenter."""
    m = 7.0
    depth = 10.0
    mmi_near = mmi_at(m, r_km=1.0, depth_km=depth)
    mmi_mid = mmi_at(m, r_km=15.0, depth_km=depth)
    mmi_far = mmi_at(m, r_km=50.0, depth_km=depth)

    assert 0.0 <= mmi_far < mmi_mid < mmi_near <= 12.0
    assert mmi_near > 8.0  # Strong near-field shaking for M7


def test_collapse_probability_interpolation():
    """Verify piecewise linear fragility curve returns correct probabilities."""
    assert collapse_probability(5.0) == 0.0
    assert collapse_probability(6.5) == 0.0
    assert collapse_probability(12.0) == 0.55
    assert collapse_probability(13.0) == 0.55

    # Midpoint between 8.0 (0.025) and 9.0 (0.080) -> 0.0525
    assert pytest.approx(collapse_probability(8.5), abs=1e-4) == 0.0525


def test_evaluate_building_damage():
    """Verify damage assessment assigns valid categories and collapse modes."""
    footprint = BuildingFootprint(
        id=1,
        lng=30.73,
        lat=46.48,
        height_m=25.0,
        min_height_m=0.0,
        ring=((30.729, 46.479), (30.731, 46.479), (30.731, 46.481), (30.729, 46.481)),
        orientation_angle_rad=0.0,
        length1_m=15.0,
        length2_m=15.0,
    )
    quake = EarthquakeHypocenter(lng=30.73, lat=46.48, depth_km=10.0, magnitude=7.5)

    damage = evaluate_building_damage(footprint, quake, quality_multiplier=1.0, random_seed_val=0.05)
    assert damage.building_id == 1
    assert damage.mmi > 9.0
    assert damage.category in (0, 1, 2)
    assert 1 <= damage.mode <= 5
    assert damage.start_delay_s > 0.0


# ==============================================================================
# 6. 5-Mode Collapse Kinematics
# ==============================================================================

def test_collapse_modes_boundaries_and_shapes():
    """Verify all 5 collapse modes satisfy start k=1.0 and end k=kf."""
    k0 = 1.0
    kf = 0.15

    for mode in (1, 2, 3, 4, 5):
        # Initial state at u=0
        assert pytest.approx(collapse_k(mode, 0.0, k0, kf), abs=1e-3) == k0
        # Final state at u=1
        assert pytest.approx(collapse_k(mode, 1.0, k0, kf), abs=1e-3) == kf
        # Midpoint should be strictly between k0 and kf
        mid_k = collapse_k(mode, 0.5, k0, kf)
        assert kf <= mid_k <= k0

    # Soft-storey (mode 2) holds flat between u=0.12 and u=0.5
    k_early = collapse_k(2, 0.2, k0, kf, height_m=30.0)
    k_mid = collapse_k(2, 0.45, k0, kf, height_m=30.0)
    assert pytest.approx(k_early, abs=1e-3) == k_mid


# ==============================================================================
# 7. Oriented Bounding Box (OBB) Derivation
# ==============================================================================

def test_oriented_bounding_box_computation():
    """Verify longest-edge angle and bounding dimensions from polygon footprint."""
    origin_lng, origin_lat = 30.73, 46.48
    # Define rectangular footprint rotated by 0 rad: 30m east by 20m north
    kx = 111320.0 * math.cos(origin_lat * math.pi / 180.0)
    ky = 110574.0

    dlng = 30.0 / kx
    dlat = 20.0 / ky

    ring = (
        (origin_lng, origin_lat),
        (origin_lng + dlng, origin_lat),
        (origin_lng + dlng, origin_lat + dlat),
        (origin_lng, origin_lat + dlat),
    )

    cx, cy, ang, l1, l2 = compute_oriented_bounding_box(ring, origin_lng, origin_lat)

    assert pytest.approx(l1, abs=1.0) == 30.0
    assert pytest.approx(l2, abs=1.0) == 20.0
    assert pytest.approx(cx, abs=1.0) == 15.0
    assert pytest.approx(cy, abs=1.0) == 10.0


# ==============================================================================
# 8. Rigid Body Kinematics & Container Shake
# ==============================================================================

def test_rigid_body_tip_step_clamps():
    """Verify angular acceleration and speed clamps prevent numerical explosion."""
    height = 20.0
    th = 0.5  # 28 degrees lean
    w = 1.0
    dt = 0.02

    th_next, w_next = simulate_rigid_body_tip_step(height, th, w, dt)
    assert th_next > th
    assert w_next > w
    assert w_next <= 2.5  # Max angular velocity clamp
    assert (th_next - th) <= 0.09  # Max frame angular step clamp


def test_container_shake_frame_envelope():
    """Verify container shake buildup, decay, and frequency chirp."""
    mag = 7.0
    duration = 5000.0

    # Buildup phase (t = 1000ms / 5000ms = 0.20 < 0.35)
    f_early = compute_container_shake_frame(1000.0, duration, mag)
    # Peak / early decay phase (t = 2000ms / 5000ms = 0.40)
    f_peak = compute_container_shake_frame(2000.0, duration, mag)
    # Late decay phase (t = 4500ms / 5000ms = 0.90)
    f_late = compute_container_shake_frame(4500.0, duration, mag)

    assert f_early.envelope < f_peak.envelope
    assert f_late.envelope < f_peak.envelope
    assert 7.0 <= f_early.omega_radps <= 46.0
    assert f_peak.scale >= 1.0


# ==============================================================================
# 9. SkillValidator & SkillCardParser Craft Standards (Rules 34, 37, 44)
# ==============================================================================

def test_skill_validator_and_card_parser():
    """Verify geospatial-disaster-simulation passes SkillValidator and SkillCardParser."""
    from harness.creator.skills import SkillValidator
    from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser

    skill_dir = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "geospatial-disaster-simulation"
    report = SkillValidator.validate_sync(skill_dir)
    assert report.valid is True
    assert len(report.errors) == 0
    assert len(report.warnings) == 0

    node = SkillCardParser.parse_directory(skill_dir)
    assert node is not None
    assert node.name == "geospatial-disaster-simulation"
    assert len(node.stages) == 5
    assert len(node.anti_patterns) >= 5
    assert len(node.invariants) >= 5

