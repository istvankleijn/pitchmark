import altair as alt
import numpy as np
import open3d as o3d
import shapely

import pitchmark.geom as geom
import pitchmark.physics as physics
import pitchmark.plotting as plotting


def _sloped_mesh_gdf(bounds, *, slope=0.15, crs=None):
    """A single-plane (two-triangle) mesh covering `bounds`, tilted purely in
    x (z = slope * x), so its horizontal normal direction is known and
    uniform across the whole area - unlike real LIDAR data, deterministic
    and CI-portable."""
    xmin, ymin, xmax, ymax = bounds
    vertices = [
        (xmin, ymin, slope * xmin),
        (xmax, ymin, slope * xmax),
        (xmin, ymax, slope * xmin),
        (xmax, ymax, slope * xmax),
    ]
    mesh = o3d.geometry.TriangleMesh(
        o3d.utility.Vector3dVector(vertices),
        o3d.utility.Vector3iVector([(0, 1, 2), (1, 3, 2)]),
    )
    return geom.gdf_from_mesh(mesh, crs=crs)


def test_multi_putt_pipeline_and_downhill_invariant(augusta_national, azalea):
    """
    Simulates putts to multiple hole locations on a real green polygon (from
    the augusta_national OSM fixture), on a synthetic sloped mesh, and
    builds the full course+incline+trajectory+hole-marker chart overlay -
    exercising osm parsing, Course/Hole construction, geom's mesh-normal
    convention, physics's rolling simulation, and plotting together in one
    pass, the way a real caller would use them.

    Also re-derives the physically load-bearing property behind
    test_simple_roll_du_downhill_accelerates_uphill_decelerates
    (physics/test_rolling.py) - but through the full roll_ball() ODE
    integration and a real green polygon, rather than calling
    simple_roll_du directly on a single hand-picked triangle - as a guard
    against the mesh-normal convention (geom.py) and the physics engine
    (physics/rolling.py) drifting out of sync with each other again.
    """
    flag = augusta_national.transformer_to_local.transform(*azalea.path.coords[-1])
    green_poly = azalea.gdf[
        azalea.gdf.contains(shapely.Point(flag))
        & (azalea.gdf["course_area"] == "putting_green")
    ].union_all()

    mesh_gdf = _sloped_mesh_gdf(green_poly.buffer(5.0).bounds, crs=azalea.gdf.crs)
    nx, ny, _ = mesh_gdf.iloc[0][["normal_x", "normal_y", "normal_z"]]
    downhill = np.array([nx, ny]) / np.hypot(nx, ny)
    center = np.array(green_poly.centroid.coords[0])

    hole_locations = {
        "near pin": tuple(center - 5.0 * downhill),
        "far pin": tuple(center + 5.0 * downhill),
    }
    start_position = tuple(center - 15.0 * downhill)

    trajectory_dfs = {}
    for label, hole_location in hole_locations.items():
        green = physics.Green(12.0, gdf=mesh_gdf, hole_location=hole_location)
        dx = hole_location[0] - start_position[0]
        dy = hole_location[1] - start_position[1]
        distance = np.hypot(dx, dy)
        theta = np.arctan2(dy, dx)
        v_init = 2.0 * np.sqrt(distance / (green.stimp / 3.0))
        vx0, vy0 = v_init * np.cos(theta), v_init * np.sin(theta)

        end_point, sol = green.roll_ball(
            *start_position, vx0, vy0, dense=True, tmax=15.0
        )
        assert sol.success, label
        trajectory_dfs[label] = plotting.trajectory_dataframe(sol)

    course_chart = plotting.chart_course(azalea.gdf.clip(green_poly.buffer(10.0)))
    incline_chart = plotting.chart_incline(mesh_gdf)
    hole_chart = plotting.chart_hole_marker(hole_locations["near pin"])
    layered = course_chart + incline_chart + hole_chart
    assert isinstance(layered, alt.LayerChart)
    for trajectory_df in trajectory_dfs.values():
        assert isinstance(plotting.chart_trajectory(trajectory_df), alt.Chart)
        assert len(trajectory_df) > 1

    # A ball hit downhill should have travelled farther after a fixed short
    # time than one hit at the same speed on a flat surface, and a ball hit
    # uphill should have travelled less far. Comparing at a fixed time
    # (rather than waiting for each to come to rest) sidesteps a real
    # numerical fragility: on a steep enough slope, a ball hit uphill
    # decelerates, stops, and rolls back down past its start - and whether
    # solve_ivp's adaptive stepping catches that brief near-zero-speed
    # instant depends on unrelated integration settings like tmax, not on
    # anything pitchmark controls.
    v_test = 1.0
    t_check = 1.0
    flat_surf = physics.Surface(12.0)
    sloped_surf = physics.Surface(12.0, gdf=mesh_gdf)

    _, flat_sol = flat_surf.roll_ball(0.0, 0.0, *(v_test * downhill), dense=True)
    _, downhill_sol = sloped_surf.roll_ball(*center, *(v_test * downhill), dense=True)
    _, uphill_sol = sloped_surf.roll_ball(*center, *(-v_test * downhill), dense=True)

    flat_distance = np.hypot(*flat_sol.sol(t_check)[:2])
    downhill_distance = np.hypot(*(downhill_sol.sol(t_check)[:2] - center))
    uphill_distance = np.hypot(*(uphill_sol.sol(t_check)[:2] - center))

    assert downhill_distance > flat_distance > uphill_distance
