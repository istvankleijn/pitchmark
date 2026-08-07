import altair as alt
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from pitchmark.physics.rolling import HOLE_RADIUS

_palette = {
    "water": "RoyalBlue",
    "sand": "Khaki",
    "green": "Aquamarine",
    "short_grass": "LawnGreen",
    "woods": "ForestGreen",
    "long_grass": "LimeGreen",
}


def chart_course(geodataframe, *, mode="ground_cover", tooltip=True):
    match mode:
        case "ground_cover":
            _domain = list(_palette.keys())
            _range = list(_palette.values())
        case _:
            raise ValueError(f"{mode=} not implemented")

    if tooltip is True:
        tooltip = ["name", "ground_cover", "course_area"]
    elif tooltip in (False, None):
        tooltip = alt.value(None)

    course_chart = (
        alt.Chart(geodataframe.sort_values(by=mode, ascending=False))
        .mark_geoshape()
        .encode(
            color=alt.Color(
                mode,
                scale=alt.Scale(
                    domain=_domain,
                    range=_range,
                ),
            ),
            tooltip=tooltip,
        )
        .project(type="identity", reflectY=True)
    )
    return course_chart


def _resolve_tooltip(tooltip, columns):
    if tooltip is True:
        return columns
    elif tooltip in (False, None):
        return alt.value(None)
    return tooltip


def chart_grade(geodataframe, *, tooltip=True):
    """
    Chart a mesh GeoDataFrame's triangles shaded by slope steepness.

    Parameters:

    geodataframe: geopandas.GeoDataFrame
        Must have a ``slope_grade`` column, e.g. as produced by
        :func:`pitchmark.geom.gdf_from_mesh`.
    tooltip: bool or list, default True
        If True, show the default tooltip columns. If False or None, disable
        the tooltip. Otherwise, an explicit list of columns to show.
    """
    tooltip = _resolve_tooltip(tooltip, ["x", "y", "z", "slope_heading", "slope_grade"])
    return (
        alt.Chart(geodataframe)
        .mark_geoshape()
        .encode(
            color=alt.Color("slope_grade", scale=alt.Scale(scheme="greys")),
            tooltip=tooltip,
        )
        .project(type="identity", reflectY=True)
    )


def chart_incline(geodataframe, *, tooltip=True):
    """
    Chart a mesh GeoDataFrame's triangles as wedge markers pointing downslope.

    Parameters:

    geodataframe: geopandas.GeoDataFrame
        Must have ``x``, ``y``, ``slope_heading``, and ``slope_grade``
        columns, e.g. as produced by :func:`pitchmark.geom.gdf_from_mesh`.
    tooltip: bool or list, default True
        If True, show the default tooltip columns. If False or None, disable
        the tooltip. Otherwise, an explicit list of columns to show.
    """
    tooltip = _resolve_tooltip(tooltip, ["x", "y", "z", "slope_heading", "slope_grade"])
    return (
        alt.Chart(geodataframe)
        .mark_point(shape="wedge", filled=True)
        .encode(
            longitude="x",
            latitude="y",
            angle="slope_heading",
            size="slope_grade",
            tooltip=tooltip,
        )
    )


def trajectory_dataframe(sol, *, dt=0.04, n=None):
    """
    Sample a dense-output ``solve_ivp`` result into a tidy trajectory DataFrame.

    Parameters:

    sol: scipy.integrate.OdeSolution
        The dense-output solution returned as the second element of
        :meth:`pitchmark.physics.Surface.roll_ball` when called with
        ``dense=True``.
    dt: float, default 0.04
        Fixed time interval, in seconds, between samples. The solution's
        final time point is always included, even if it falls short of a
        full interval past the previous sample. Ignored if ``n`` is given.
    n: int or None, default None
        If given, sample exactly ``n`` evenly-spaced time points instead of
        using a fixed time interval.

    Returns: pandas.DataFrame
        Columns ``t``, ``x``, ``y``, ``vx``, ``vy``, ``v`` (speed).
    """
    if n is None:
        t_eval = np.append(np.arange(sol.t[0], sol.t[-1], dt), sol.t[-1])
    else:
        t_eval = np.linspace(sol.t[0], sol.t[-1], n)
    x, y, vx, vy = sol.sol(t_eval)
    return pd.DataFrame(
        {
            "t": t_eval,
            "x": x,
            "y": y,
            "vx": vx,
            "vy": vy,
            "v": np.hypot(vx, vy),
        }
    )


def chart_trajectory(trajectory_df, *, tooltip=True):
    """
    Chart a ball's trajectory as points colored by speed.

    Parameters:

    trajectory_df: pandas.DataFrame
        As produced by :func:`trajectory_dataframe`.
    tooltip: bool or list, default True
        If True, show the default tooltip columns. If False or None, disable
        the tooltip. Otherwise, an explicit list of columns to show.
    """
    tooltip = _resolve_tooltip(tooltip, ["t", "x", "y", "v"])
    return (
        alt.Chart(trajectory_df)
        .mark_point(clip=True)
        .encode(
            longitude="x",
            latitude="y",
            color="v",
            tooltip=tooltip,
        )
    )


def chart_hole_marker(hole_location, *, hole_radius=HOLE_RADIUS):
    """
    Chart a basic marker at a hole's location.

    Parameters:

    hole_location: tuple of float
        (x, y) coordinates of the hole.
    hole_radius: float, default pitchmark.physics.rolling.HOLE_RADIUS
        Radius of the marker, in the same units as ``hole_location``.
    """
    geodataframe = gpd.GeoDataFrame(
        geometry=[shapely.buffer(shapely.Point(hole_location), hole_radius)]
    )
    return alt.Chart(geodataframe).mark_geoshape(color="black")
