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

_course_area_palette = {
    "penalty_area": "Crimson",
    "bunker": "SandyBrown",
    "putting_green": "MediumSeaGreen",
    "teeing_area": "CornflowerBlue",
    "general_area": "PaleGreen",
}


def chart_course(geodataframe, *, mode="ground_cover", tooltip=True, legend=True):
    """
    Chart a course/hole GeoDataFrame's features, colored by ground cover.

    Does not apply its own projection, so that it can be layered with
    other unprojected charts under one shared projection instead of each
    layer fighting over its own. If charting this on its own, follow it
    with ``.project(type="identity", reflectY=True)`` to plot the raw
    local x/y coordinates directly and flip the y-axis to match standard
    screen orientation.

    Parameters:

    geodataframe: geopandas.GeoDataFrame
        Must have ``ground_cover``, ``course_area``, and ``name`` columns.
    mode: str, default "ground_cover"
        Which column to color by. ``"ground_cover"`` colors by physical
        appearance (water/sand/green/short_grass/woods/long_grass).
        ``"course_area"`` colors by Rules of Golf classification
        (penalty_area/bunker/putting_green/teeing_area/general_area) -
        coarser than ``ground_cover``, since fairway, woods, and rough are
        all just "general_area" under the rules. Any other value raises
        ``ValueError``.
    tooltip: bool or list, default True
        If True, show the default tooltip columns (``name``,
        ``ground_cover``, ``course_area``). If False or None, disable the
        tooltip. Otherwise, pass an explicit list of columns to show
        instead.
    legend: bool or altair.Legend, default True
        If True, show the default legend. If False or None, suppress it -
        useful when combining several charts and relocating one shared
        legend elsewhere. Otherwise, an explicit ``altair.Legend`` to
        control its position, orientation, or layout directly.
    """
    match mode:
        case "ground_cover":
            _domain = list(_palette.keys())
            _range = list(_palette.values())
        case "course_area":
            _domain = list(_course_area_palette.keys())
            _range = list(_course_area_palette.values())
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
                **_resolve_legend(legend),
            ),
            tooltip=tooltip,
        )
    )
    return course_chart


def _resolve_tooltip(tooltip, columns):
    if tooltip is True:
        return columns
    elif tooltip in (False, None):
        return alt.value(None)
    return tooltip


def _resolve_legend(legend):
    if legend is True:
        return {}
    elif legend in (False, None):
        return {"legend": None}
    return {"legend": legend}


def chart_grade(geodataframe, *, tooltip=True, legend=True):
    """
    Chart a mesh GeoDataFrame's triangles shaded by slope steepness.

    Does not apply its own projection, so that it can be layered with
    other unprojected charts under one shared projection instead of each
    layer fighting over its own. If charting this on its own, follow it
    with ``.project(type="identity", reflectY=True)`` to plot the raw
    local x/y coordinates directly and flip the y-axis to match standard
    screen orientation.

    Parameters:

    geodataframe: geopandas.GeoDataFrame
        Must have ``x``, ``y``, ``z``, ``slope_heading``, and
        ``slope_grade`` columns describing each mesh triangle's location,
        elevation, and steepness (``slope_grade`` as a percentage).
    tooltip: bool or list, default True
        If True, show the default tooltip columns (``x``, ``y``, ``z``,
        ``slope_heading``, ``slope_grade``). If False or None, disable the
        tooltip. Otherwise, pass an explicit list of columns to show
        instead.
    legend: bool or altair.Legend, default True
        If True, show the default legend. If False or None, suppress it -
        useful when combining several charts and relocating one shared
        legend elsewhere. Otherwise, an explicit ``altair.Legend`` to
        control its position, orientation, or layout directly.
    """
    tooltip = _resolve_tooltip(tooltip, ["x", "y", "z", "slope_heading", "slope_grade"])
    return (
        alt.Chart(geodataframe)
        .mark_geoshape()
        .encode(
            color=alt.Color(
                "slope_grade",
                scale=alt.Scale(scheme="greys"),
                **_resolve_legend(legend),
            ),
            tooltip=tooltip,
        )
    )


def chart_incline(
    geodataframe,
    *,
    tooltip=True,
    hover=False,
    interactive_size_max=False,
    legend=True,
):
    """
    Chart a mesh GeoDataFrame's triangles as wedge markers pointing downslope.

    By default, wedges are drawn in a fixed color (not data-encoded) chosen
    to stand out against both :func:`chart_course`'s ground-cover palette
    and :func:`chart_trajectory`'s color scale, since the three are
    commonly layered together.

    Parameters:

    geodataframe: geopandas.GeoDataFrame
        Must have ``x``, ``y``, ``slope_heading``, and ``slope_grade``
        columns, e.g. as produced by :func:`pitchmark.geom.gdf_from_mesh`.
    tooltip: bool or list, default True
        If True, show the default tooltip columns. If False or None, disable
        the tooltip. Otherwise, an explicit list of columns to show.
    hover: bool, default False
        If True, the wedge nearest the pointer turns red on hover - makes
        individual wedges easier to target, since they can be very small.
    interactive_size_max: bool, default False
        If True, adds a range-slider control bound to the chart that caps
        the ``slope_grade`` size scale's upper bound - useful when a few
        very steep triangles (e.g. bunker edges) would otherwise dominate
        the size scale and hide subtler slopes elsewhere.
    legend: bool or altair.Legend, default True
        If True, show the default ``slope_grade`` size legend. If False or
        None, suppress it - useful when combining several charts and
        relocating one shared legend elsewhere. Otherwise, an explicit
        ``altair.Legend`` to control its position, orientation, or layout
        directly.
    """
    tooltip = _resolve_tooltip(tooltip, ["x", "y", "z", "slope_heading", "slope_grade"])
    mark_kwargs = {"shape": "wedge", "filled": True, "clip": True}
    encoding = {
        "longitude": "x",
        "latitude": "y",
        "angle": "slope_heading",
        "tooltip": tooltip,
    }
    params = []

    if hover:
        hover_param = alt.selection_point(on="pointerover", nearest=True, empty=False)
        params.append(hover_param)
        encoding["color"] = alt.condition(
            hover_param, alt.value("red"), alt.value("DarkViolet")
        )
    else:
        mark_kwargs["color"] = "DarkViolet"

    size_kwargs = _resolve_legend(legend)
    if interactive_size_max:
        grade_max = alt.param(
            value=float(geodataframe["slope_grade"].quantile(0.9)),
            bind=alt.binding_range(
                min=1.0,
                max=float(geodataframe["slope_grade"].max()),
                step=1.0,
                name="Max slope grade shown at full size: ",
            ),
        )
        params.append(grade_max)
        encoding["size"] = alt.Size(
            "slope_grade", scale=alt.Scale(domainMax=grade_max), **size_kwargs
        )
    else:
        encoding["size"] = (
            "slope_grade" if not size_kwargs else alt.Size("slope_grade", **size_kwargs)
        )

    chart = alt.Chart(geodataframe).mark_point(**mark_kwargs).encode(**encoding)
    if params:
        chart = chart.add_params(*params)
    return chart


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


def chart_trajectory(trajectory_df, *, tooltip=True, legend=True):
    """
    Chart a ball's trajectory as points colored by speed.

    Uses a fixed "oranges" sequential scale, chosen to stand out against
    both :func:`chart_course`'s ground-cover palette and
    :func:`chart_incline`'s wedge color, since the three are commonly
    layered together.

    Parameters:

    trajectory_df: pandas.DataFrame
        As produced by :func:`trajectory_dataframe`.
    tooltip: bool or list, default True
        If True, show the default tooltip columns. If False or None, disable
        the tooltip. Otherwise, an explicit list of columns to show.
    legend: bool or altair.Legend, default True
        If True, show the default ``v`` (speed) legend. If False or None,
        suppress it - useful when combining several charts and relocating
        one shared legend elsewhere. Otherwise, an explicit
        ``altair.Legend`` to control its position, orientation, or layout
        directly.
    """
    tooltip = _resolve_tooltip(tooltip, ["t", "x", "y", "v"])
    return (
        alt.Chart(trajectory_df)
        .mark_point(clip=True)
        .encode(
            longitude="x",
            latitude="y",
            color=alt.Color(
                "v", scale=alt.Scale(scheme="oranges"), **_resolve_legend(legend)
            ),
            tooltip=tooltip,
        )
    )


def chart_trajectories(trajectory_dfs, **kwargs):
    """
    Chart multiple ball trajectories together, sharing one "v" color scale
    and legend.

    Layering several :func:`chart_trajectory` calls directly (e.g. via
    ``+``) gives each its own locally-scaled color legend, so a chart with
    5 putts ends up with 5 identical-looking "v" legends stacked on top of
    each other. This resolves the color scale and legend to be shared
    across all of them instead.

    Parameters:

    trajectory_dfs: iterable of pandas.DataFrame
        Each as produced by :func:`trajectory_dataframe`.
    **kwargs:
        Passed through to each :func:`chart_trajectory` call.

    Returns: altair.LayerChart
    """
    layer = alt.layer(*(chart_trajectory(df, **kwargs) for df in trajectory_dfs))
    return layer.resolve_scale(color="shared").resolve_legend(color="shared")


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
