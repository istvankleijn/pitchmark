import geopandas as gpd
import numpy as np
import open3d as o3d
import pytest

import pitchmark.geom as geom
import pitchmark.physics as physics
from pitchmark.physics.rolling import MinBallSpeed

# Physics constants are in yards/seconds; tag fixtures accordingly, matching
# conftest.py's circle10_gdf convention.
YARD_CRS = "+proj=tmerc +ellps=WGS84 +units=yd +vunits=yd"

# Golf-ball speed leaving a Stimpmeter, in yd/s (== 6.0 ft/s).
STIMP_INIT_SPEED = 6.0 / 3.0


def _mesh_gdf(vertices):
    """Build a single-triangle GeoDataFrame the same way production code does."""
    mesh = o3d.geometry.TriangleMesh(
        o3d.utility.Vector3dVector(vertices),
        o3d.utility.Vector3iVector([(0, 1, 2)]),
    )
    return geom.gdf_from_mesh(mesh, crs=YARD_CRS)


def test_softness():
    # Independently reconstructed from the physical derivation in softness()'s
    # docstring, not by calling softness() itself.
    gravity = 9.8 / (3 * 0.3048)  # yd/s^2
    for stimp_ft in (6.0, 10.0):
        stimp_yd = stimp_ft / 3.0
        expected = (STIMP_INIT_SPEED**2) * 1.4 / (2 * gravity * stimp_yd)
        assert physics.softness(stimp_ft) == pytest.approx(expected)


@pytest.mark.parametrize(
    "stimp, gdf",
    [
        (6.0, None),
        (6.0, gpd.GeoDataFrame()),
    ],
)
def test_Surface_init(stimp, gdf):
    surf = physics.Surface(stimp, gdf=gdf)
    assert isinstance(surf, physics.Surface)
    assert isinstance(surf.gdf, gpd.GeoDataFrame)
    assert surf.stimp == stimp
    assert surf.softness == physics.softness(stimp)
    assert surf.strtree is None


def test_Surface_normal_and_z_on_mesh():
    # Tilted triangle with an exactly-known normal (mirrors test_geom.py's
    # test_gdf_from_mesh): (nx, ny, nz) = (0, -1/sqrt(17), 4/sqrt(17)).
    gdf = _mesh_gdf([(-100, -100, 0), (100, -100, 0), (-100, 100, 50)])
    surf = physics.Surface(10.0, gdf=gdf)

    normal = surf.normal(-50.0, -50.0)
    assert normal == pytest.approx([0.0, -1 / np.sqrt(17), 4 / np.sqrt(17)])

    z = surf.z(-50.0, -50.0)
    assert z == pytest.approx([50.0 / 3.0])


def test_Surface_normal_and_z_off_mesh_fallback():
    gdf = _mesh_gdf([(-100, -100, 0), (100, -100, 0), (-100, 100, 50)])
    surf = physics.Surface(10.0, gdf=gdf)

    assert surf.normal(1000.0, 1000.0) == pytest.approx([0.0, 0.0, 1.0])
    assert surf.z(1000.0, 1000.0) is None


def test_roll_ball_flat_green_self_consistency():
    """
    A ball launched at Stimpmeter speed on a level green should travel almost
    exactly the Stimpmeter reading before stopping - this is the regression
    test for the g/(1+I_b) vs g/I_b prefactor bug.
    """
    gdf = _mesh_gdf([(-100, -100, 0), (100, -100, 0), (0, 100, 0)])
    stimp_ft = 10.0
    surf = physics.Surface(stimp_ft, gdf=gdf)

    end_point = surf.roll_ball(0.0, 0.0, 0.0, STIMP_INIT_SPEED)

    distance = np.hypot(end_point[0], end_point[1])
    assert distance == pytest.approx(stimp_ft / 3.0)


def test_simple_roll_du_sloped_regression():
    """
    Pins simple_roll_du's current output on a slope with an exactly-known
    normal, for a ball moving straight across the slope (vx=1, vy=0).

    This is NOT a validated physical-correctness check - which way a ball
    should curve on a slope here is a known open question (see the comment
    on simple_roll_du). It exists to catch regressions in the ported formula,
    e.g. reverting to the old grade*nx double-count or wrong prefactor.
    """
    gdf = _mesh_gdf([(-100, -100, 0), (100, -100, 0), (-100, 100, 50)])
    stimp_ft = 10.0
    surf = physics.Surface(stimp_ft, gdf=gdf)

    du = surf.simple_roll_du([-50.0, -50.0, 1.0, 0.0])

    gravity = 9.8 / (3 * 0.3048)
    expected_dvx = -(STIMP_INIT_SPEED**2) / (
        2 * (stimp_ft / 3.0)
    )  # nx=0, pure friction
    expected_dvy = 2 * gravity / (7 * np.sqrt(17))
    assert du == pytest.approx([1.0, 0.0, expected_dvx, expected_dvy])


def test_roll_ball_dense_contract():
    # No gdf -> normal() fallback makes this an effectively flat surface.
    surf = physics.Surface(10.0)

    end_point = surf.roll_ball(0.0, 0.0, 0.0, STIMP_INIT_SPEED)
    assert end_point.shape == (4,)

    end_point_dense, sol = surf.roll_ball(0.0, 0.0, 0.0, STIMP_INIT_SPEED, dense=True)
    assert end_point_dense == pytest.approx(end_point)
    assert sol.success
    assert sol.y.shape[0] == 4


def test_roll_ball_custom_events():
    surf = physics.Surface(10.0)
    default_end = surf.roll_ball(0.0, 0.0, 0.0, STIMP_INIT_SPEED)
    custom_end = surf.roll_ball(
        0.0, 0.0, 0.0, STIMP_INIT_SPEED, events=[MinBallSpeed(0.5)]
    )

    # A higher stop-speed threshold should terminate the roll earlier, with the
    # ball travelling a shorter distance.
    default_distance = np.hypot(default_end[0], default_end[1])
    custom_distance = np.hypot(custom_end[0], custom_end[1])
    assert custom_distance < default_distance


def test_MinBallSpeed_init():
    event = MinBallSpeed(2.0, terminal=False, direction=-1)
    assert event.min_speed == 2.0
    assert event.terminal is False
    assert event.direction == -1


def test_MinBallSpeed_init_defaults():
    event = MinBallSpeed(1e-6)
    assert event.terminal is True
    assert event.direction == 0


@pytest.mark.parametrize(
    "vx, vy, expected",
    [
        (3.0, 4.0, 21.0),  # speed 5, min_speed 2 -> 5^2 - 2^2
        (2.0, 0.0, 0.0),  # exactly at the threshold -> zero crossing
        (0.0, 0.0, -4.0),  # at rest -> negative
    ],
)
def test_MinBallSpeed_usage(vx, vy, expected):
    event = MinBallSpeed(2.0)
    assert event(0.0, [0.0, 0.0, vx, vy]) == pytest.approx(expected)


def test_Green_init():
    green = physics.Green(12.0)
    assert green.hole_location == (0.0, 0.0)
    assert green.hole_radius_squared == pytest.approx(green.hole_radius**2)
    assert green.holing_vmax == 1.63
    assert green.softness == physics.softness(12.0)


def test_Green_init_custom_hole():
    green = physics.Green(
        12.0, hole_location=(3.0, -4.0), hole_radius=0.1, holing_vmax=2.0
    )
    assert green.hole_location == (3.0, -4.0)
    assert green.hole_radius == 0.1
    assert green.hole_radius_squared == pytest.approx(0.01)
    assert green.holing_vmax == 2.0


def test_Green_usage():
    green = physics.Green(
        12.0, hole_location=(0.0, 0.0), hole_radius=0.06, holing_vmax=1.63
    )

    # At the hole center at rest: impact=0, v=0 -> 0 - 1.63*(1-0)
    assert green.impact_function([0.0, 0.0, 0.0, 0.0]) == pytest.approx(-1.63)

    # Exactly on the hole's rim (squared_distance == hole_radius_squared): impact=1
    assert green.impact_function([0.06, 0.0, 0.0, 0.0]) == pytest.approx(0.0)

    # Away from the hole, moving fast: v dominates
    assert green.impact_function([10.0, 0.0, 3.0, 4.0]) == pytest.approx(
        5.0 - 1.63 * (1.0 - (10.0**2) / (0.06**2))
    )
