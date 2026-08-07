import altair as alt
import numpy as np
import open3d as o3d
import pytest

import pitchmark.geom as geom
import pitchmark.physics as physics
import pitchmark.plotting

# Physics constants are in yards/seconds; tag fixtures accordingly, matching
# conftest.py's circle10_gdf and test_rolling.py's YARD_CRS convention.
YARD_CRS = "+proj=tmerc +ellps=WGS84 +units=yd +vunits=yd"
STIMP_INIT_SPEED = 6.0 / 3.0


def _mesh_gdf(vertices):
    """Build a single-triangle GeoDataFrame the same way production code does."""
    mesh = o3d.geometry.TriangleMesh(
        o3d.utility.Vector3dVector(vertices),
        o3d.utility.Vector3iVector([(0, 1, 2)]),
    )
    return geom.gdf_from_mesh(mesh, crs=YARD_CRS)


@pytest.mark.parametrize(
    "mode, tooltip",
    [
        ("ground_cover", True),
        ("ground_cover", False),
        ("ground_cover", None),
        ("course_area", True),
    ],
)
def test_chart_course(augusta_national, mode, tooltip):
    gdf = augusta_national.gdf
    if mode != "ground_cover":
        with pytest.raises(ValueError, match=f"{mode=} not implemented"):
            chart = pitchmark.plotting.chart_course(gdf, mode=mode)
        return

    chart = pitchmark.plotting.chart_course(gdf, mode=mode, tooltip=tooltip)
    assert isinstance(chart, alt.Chart)

    chart_dict = chart.to_dict()
    assert chart_dict["mark"]["type"] == "geoshape"
    assert chart_dict["encoding"]["color"]["field"] == mode
    # No projection of its own - callers apply one shared projection when
    # layering chart_course with other charts (see chart_incline etc.).
    assert "projection" not in chart_dict
    if tooltip is True:
        assert chart_dict["encoding"]["tooltip"] == [
            {"field": "name", "type": "nominal"},
            {"field": "ground_cover", "type": "ordinal"},
            {"field": "course_area", "type": "ordinal"},
        ]


_DEFAULT_MESH_TOOLTIP = [
    {"field": "x", "type": "quantitative"},
    {"field": "y", "type": "quantitative"},
    {"field": "z", "type": "quantitative"},
    {"field": "slope_heading", "type": "quantitative"},
    {"field": "slope_grade", "type": "quantitative"},
]


@pytest.mark.parametrize("tooltip", [True, False, None])
def test_chart_grade(tooltip):
    gdf = _mesh_gdf([(-100, -100, 0), (100, -100, 0), (-100, 100, 50)])
    chart = pitchmark.plotting.chart_grade(gdf, tooltip=tooltip)
    assert isinstance(chart, alt.Chart)

    chart_dict = chart.to_dict()
    assert chart_dict["mark"]["type"] == "geoshape"
    assert chart_dict["encoding"]["color"]["field"] == "slope_grade"
    assert chart_dict["encoding"]["color"]["scale"]["scheme"] == "greys"
    assert "projection" not in chart_dict
    if tooltip is True:
        assert chart_dict["encoding"]["tooltip"] == _DEFAULT_MESH_TOOLTIP
    else:
        assert chart_dict["encoding"]["tooltip"] == {"value": None}


@pytest.mark.parametrize("tooltip", [True, False, None])
def test_chart_incline(tooltip):
    gdf = _mesh_gdf([(-100, -100, 0), (100, -100, 0), (-100, 100, 50)])
    chart = pitchmark.plotting.chart_incline(gdf, tooltip=tooltip)
    assert isinstance(chart, alt.Chart)

    chart_dict = chart.to_dict()
    assert chart_dict["mark"]["type"] == "point"
    assert chart_dict["mark"]["shape"] == "wedge"
    assert chart_dict["mark"]["filled"] is True
    assert chart_dict["mark"]["color"] == "DarkViolet"
    assert chart_dict["encoding"]["longitude"]["field"] == "x"
    assert chart_dict["encoding"]["latitude"]["field"] == "y"
    assert chart_dict["encoding"]["angle"]["field"] == "slope_heading"
    assert chart_dict["encoding"]["size"]["field"] == "slope_grade"
    if tooltip is True:
        assert chart_dict["encoding"]["tooltip"] == _DEFAULT_MESH_TOOLTIP
    else:
        assert chart_dict["encoding"]["tooltip"] == {"value": None}


def test_chart_grade_custom_tooltip():
    gdf = _mesh_gdf([(-100, -100, 0), (100, -100, 0), (-100, 100, 50)])
    chart = pitchmark.plotting.chart_grade(gdf, tooltip=["slope_grade"])
    chart_dict = chart.to_dict()
    assert chart_dict["encoding"]["tooltip"] == [
        {"field": "slope_grade", "type": "quantitative"}
    ]


def test_trajectory_dataframe():
    surf = physics.Surface(10.0)
    # Off-axis launch so vx and vy are both consistently nonzero throughout -
    # a straight-up-the-y-axis launch would leave vx==0 for the whole roll on
    # a flat surface, making a vx+vy vs. hypot(vx, vy) mutation undetectable.
    vx0 = vy0 = STIMP_INIT_SPEED / np.sqrt(2)
    _, sol = surf.roll_ball(0.0, 0.0, vx0, vy0, dense=True)

    df = pitchmark.plotting.trajectory_dataframe(sol, n=50)
    assert list(df.columns) == ["t", "x", "y", "vx", "vy", "v"]
    assert len(df) == 50
    assert df["t"].iloc[0] == pytest.approx(sol.t[0])
    assert df["t"].iloc[-1] == pytest.approx(sol.t[-1])
    assert (df["v"] == (df["vx"] ** 2 + df["vy"] ** 2) ** 0.5).all()


def test_trajectory_dataframe_default_dt():
    surf = physics.Surface(10.0)
    _, sol = surf.roll_ball(0.0, 0.0, 0.0, STIMP_INIT_SPEED, dense=True)

    df = pitchmark.plotting.trajectory_dataframe(sol)
    # Fixed dt=0.04s intervals, plus the exact final time point appended.
    expected_samples = len(np.arange(sol.t[0], sol.t[-1], 0.04)) + 1
    assert len(df) == expected_samples
    assert df["t"].iloc[-1] == pytest.approx(sol.t[-1])
    # Interior spacing is the fixed dt; only the final gap may be shorter.
    assert df["t"].diff().iloc[1:-1].to_numpy() == pytest.approx(0.04)


def test_trajectory_dataframe_custom_dt():
    surf = physics.Surface(10.0)
    _, sol = surf.roll_ball(0.0, 0.0, 0.0, STIMP_INIT_SPEED, dense=True)

    df = pitchmark.plotting.trajectory_dataframe(sol, dt=0.1)
    assert df["t"].iloc[-1] == pytest.approx(sol.t[-1])
    assert df["t"].diff().iloc[1:-1].to_numpy() == pytest.approx(0.1)


def test_trajectory_dataframe_n_overrides_dt():
    surf = physics.Surface(10.0)
    _, sol = surf.roll_ball(0.0, 0.0, 0.0, STIMP_INIT_SPEED, dense=True)

    df = pitchmark.plotting.trajectory_dataframe(sol, dt=0.1, n=50)
    assert len(df) == 50


@pytest.mark.parametrize("tooltip", [True, False, None])
def test_chart_trajectory(tooltip):
    surf = physics.Surface(10.0)
    _, sol = surf.roll_ball(0.0, 0.0, 0.0, STIMP_INIT_SPEED, dense=True)
    df = pitchmark.plotting.trajectory_dataframe(sol, n=10)

    chart = pitchmark.plotting.chart_trajectory(df, tooltip=tooltip)
    assert isinstance(chart, alt.Chart)

    chart_dict = chart.to_dict()
    assert chart_dict["mark"]["type"] == "point"
    assert chart_dict["mark"]["clip"] is True
    assert chart_dict["encoding"]["longitude"]["field"] == "x"
    assert chart_dict["encoding"]["latitude"]["field"] == "y"
    assert chart_dict["encoding"]["color"]["field"] == "v"
    assert chart_dict["encoding"]["color"]["scale"]["scheme"] == "oranges"
    if tooltip is True:
        assert chart_dict["encoding"]["tooltip"] == [
            {"field": "t", "type": "quantitative"},
            {"field": "x", "type": "quantitative"},
            {"field": "y", "type": "quantitative"},
            {"field": "v", "type": "quantitative"},
        ]
    else:
        assert chart_dict["encoding"]["tooltip"] == {"value": None}


def test_chart_hole_marker():
    chart = pitchmark.plotting.chart_hole_marker((3.0, -4.0))
    assert isinstance(chart, alt.Chart)

    chart_dict = chart.to_dict()
    assert chart_dict["mark"]["type"] == "geoshape"
    assert chart_dict["mark"]["color"] == "black"

    (geometry,) = chart.data.geometry
    assert geometry.centroid.x == pytest.approx(3.0)
    assert geometry.centroid.y == pytest.approx(-4.0)


def test_chart_hole_marker_custom_radius():
    small = pitchmark.plotting.chart_hole_marker((0.0, 0.0), hole_radius=0.01)
    large = pitchmark.plotting.chart_hole_marker((0.0, 0.0), hole_radius=1.0)

    (small_geom,) = small.data.geometry
    (large_geom,) = large.data.geometry
    assert large_geom.area > small_geom.area
