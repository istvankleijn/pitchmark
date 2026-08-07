"""
Exploratory visual check of the rolling physics on a real, topologically
complex green: Augusta National hole 1 ("Tea Olive"). Simulates 5 putts,
all launched at the same speed from the same distance but spread evenly
around the hole, to see whether the slope curves each one the way the
terrain suggests it should (this is what originally caught and helped
confirm the fix for a slope-direction sign bug in
pitchmark.physics.rolling.simple_roll_du - see git history around
"fix: correct slope-direction sign in simple_roll_du").

Requires a real LIDAR mesh for the hole, built once from local elevation
data and cached to CSV (gitignored, not in the repo - regenerate via
Course.populate_hole_meshes(), or the equivalent per-hole delaunay3d/
simplified_mesh/gdf_from_mesh pipeline, against a local LAS/LAZ ground
point cloud):

    data-raw/USGS_LIDAR/tea_olive_mesh.csv

This is exploratory/scratch, not part of the package or its test suite -
not linted or type-checked the way src/ and tests/ are.
"""

import pathlib

import altair as alt
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

import pitchmark
import pitchmark.osm
import pitchmark.physics as physics
import pitchmark.plotting as plotting

ROOT = pathlib.Path(__file__).resolve().parent.parent

handler = pitchmark.osm.GolfHandler()
handler.apply_file(ROOT / "tests" / "augusta_national.osm")
fc = handler.feature_collection
augusta_national = pitchmark.Course.from_featurecollection(fc)
tea_olive = augusta_national.holes[0]

mesh_path = ROOT / "data-raw" / "USGS_LIDAR" / "tea_olive_mesh.csv"
mesh_df = pd.read_csv(mesh_path, index_col=0)
mesh_df["geometry"] = gpd.GeoSeries.from_wkt(mesh_df["geometry"])
mesh_gdf = gpd.GeoDataFrame(mesh_df, crs=tea_olive.gdf.crs)

flag = augusta_national.transformer_to_local.transform(*tea_olive.path.coords[-1])
green_poly = tea_olive.gdf[
    tea_olive.gdf.contains(shapely.Point(flag))
    & (tea_olive.gdf["course_area"] == "putting_green")
].union_all()
green_mesh = mesh_gdf[mesh_gdf.geometry.centroid.within(green_poly)]

softness = physics.softness(12.0)
# A ball at rest stays at rest only where grade/100 < softness/ball_moi -
# below that, even the most favorable (straight downhill) direction
# decelerates; above it, rolling away is inevitable. See simple_roll_du's
# dv_forward: at the boundary, ball_moi * (grade/100) == softness.
still_enough_for_ball = green_mesh[
    green_mesh["slope_grade"] / 100.0 < softness / physics.rolling.MOI_SOLID_SPHERE
]
flat_enough_for_hole = green_mesh[green_mesh["slope_grade"] < 2.0]


def _nearest(candidates, point):
    d2 = (candidates["x"] - point[0]) ** 2 + (candidates["y"] - point[1]) ** 2
    return tuple(candidates.loc[d2.idxmin(), ["x", "y"]])


def _angular_spread_sample(candidates, n, *, center):
    """Greedily pick n points at (roughly) the candidates' shared distance
    from `center`, maximizing angular separation between them - so they're
    spread around the hole like numbers on a clock, all the same distance
    away, rather than clustered on one side."""
    xy = candidates[["x", "y"]].to_numpy()
    angles = np.degrees(np.arctan2(xy[:, 1] - center[1], xy[:, 0] - center[0])) % 360

    def circular_distance(a, b):
        d = np.abs(a - b) % 360
        return np.minimum(d, 360 - d)

    chosen = [0]
    for _ in range(n - 1):
        min_dists = np.min(
            [circular_distance(angles, angles[i]) for i in chosen], axis=0
        )
        chosen.append(int(np.argmax(min_dists)))
    return [tuple(xy[i]) for i in chosen]


hole_location = _nearest(flat_enough_for_hole, flag)

# All 5 starts at (roughly) the same distance from the hole, so any
# difference in how far a putt travels is purely the slope's doing, not a
# difference in starting distance too.
radius, tolerance = 12.0, 0.5
distance_to_hole = np.hypot(
    still_enough_for_ball["x"] - hole_location[0],
    still_enough_for_ball["y"] - hole_location[1],
)
ring_candidates = still_enough_for_ball[
    (distance_to_hole > radius - tolerance) & (distance_to_hole < radius + tolerance)
]
start_points = _angular_spread_sample(ring_candidates, 5, center=hole_location)
start_positions = {f"start {i + 1}": pos for i, pos in enumerate(start_points)}

green = physics.Green(12.0, gdf=mesh_gdf, hole_location=hole_location)

# One shared launch speed for every putt (calibrated to the shared
# straight-line distance, on a flat-green basis), so any difference in how
# far each one actually travels is the slope's doing, not a difference in
# how hard it was hit.
distances = {
    label: np.hypot(hole_location[0] - pos[0], hole_location[1] - pos[1])
    for label, pos in start_positions.items()
}
v_init = 2.0 * np.sqrt(np.mean(list(distances.values())) / (green.stimp / 3))

results = {}
for label, pos in start_positions.items():
    dx = hole_location[0] - pos[0]
    dy = hole_location[1] - pos[1]
    theta_init = np.arctan2(dy, dx)
    vx0, vy0 = v_init * np.cos(theta_init), v_init * np.sin(theta_init)

    end_point, sol = green.roll_ball(pos[0], pos[1], vx0, vy0, dense=True, tmax=15.0)
    travelled = np.hypot(end_point[0] - pos[0], end_point[1] - pos[1])
    miss_distance = np.hypot(
        end_point[0] - hole_location[0], end_point[1] - hole_location[1]
    )
    print(
        f"{label}: distance to hole={distances[label]:.1f}yd, "
        f"travelled={travelled:.1f}yd, miss={miss_distance:.2f}yd"
    )
    results[label] = (pos, plotting.trajectory_dataframe(sol))

margin = 8.0
all_x = [hole_location[0]] + [pos[0] for pos, _ in results.values()]
all_y = [hole_location[1]] + [pos[1] for pos, _ in results.values()]
xmin, xmax = min(all_x) - margin, max(all_x) + margin
ymin, ymax = min(all_y) - margin, max(all_y) + margin
region_shell = shapely.box(xmin, ymin, xmax, ymax)

region_course = tea_olive.gdf.clip(region_shell)
# A rectangular .cx[] bbox slice isn't enough - the mesh extends into
# unclassified terrain (tree lines, out-of-bounds ground) that has no
# course-area polygon drawn there at all, so wedges would float in blank
# background. Keep only triangles actually within a drawn course polygon.
course_union = region_course.union_all()
region_mesh = mesh_gdf.cx[xmin:xmax, ymin:ymax]
region_mesh = region_mesh[region_mesh.geometry.centroid.within(course_union)]

# legend=False on all three - their legends are relocated below the
# overview panel instead (via small proxy charts further down), rather
# than attached to this 800px map.
course_chart = plotting.chart_course(region_course, legend=False)

# Cap the size scale at the same "would a ball actually stay put here"
# threshold used to pick start positions (grade/100 == softness/ball_moi -
# see the comment near still_enough_for_ball above), via Vega-Lite's
# scale `clamp` rather than a slider: wedges at or below the threshold are
# sized normally, and anything steeper renders at that same max size (not
# larger) since size stops being a meaningful comparison past that point -
# but colored paler, to flag "no putt could ever rest here" rather than
# implying an even steeper, more informative size.
max_stable_grade = 100.0 * softness / physics.rolling.MOI_SOLID_SPHERE
_hover_param = alt.selection_point(on="pointerover", nearest=True, empty=False)
_too_steep = f"datum.slope_grade > {max_stable_grade}"
incline_chart = (
    alt.Chart(region_mesh)
    .add_params(_hover_param)
    .mark_point(shape="wedge", filled=True, clip=True)
    .encode(
        longitude="x",
        latitude="y",
        angle="slope_heading",
        size=alt.Size(
            "slope_grade",
            scale=alt.Scale(domain=[0, max_stable_grade], clamp=True),
            legend=None,
        ),
        # Altair's alt.condition() can't nest (both calls try to set the
        # same underlying "condition" key), so chained conditions - hover
        # wins over too-steep-to-matter - need the list form instead.
        color=alt.Color(
            condition=[
                {"param": _hover_param.param.name, "empty": False, "value": "red"},
                {"test": _too_steep, "value": "Plum"},
            ],
            value="DarkViolet",
        ),
        tooltip=["x", "y", "z", "slope_heading", "slope_grade"],
    )
)
hole_chart = plotting.chart_hole_marker(
    hole_location, hole_radius=5 * physics.rolling.HOLE_RADIUS
)

start_charts = []
trajectory_dfs = []
for label, (pos, trajectory_df) in results.items():
    start_df = pd.DataFrame({"x": [pos[0]], "y": [pos[1]]})
    start_charts.append(
        alt.Chart(start_df)
        .mark_point(shape="triangle-up", size=300, filled=True, color="black")
        .encode(longitude="x", latitude="y")
    )
    trajectory_dfs.append(trajectory_df)

trajectory_layer = plotting.chart_trajectories(trajectory_dfs, legend=False)

# Hole marker last, so it draws on top and isn't obscured by trajectories
# passing over/near it. Compass moved to the overview panel (see below).
combined = course_chart + incline_chart + trajectory_layer
for start_chart in start_charts:
    combined = combined + start_chart
combined = combined + hole_chart

combined = combined.project(type="identity", reflectY=True).properties(
    width=800,
    height=800,
    title="Tea Olive (hole 1) - multiple putts to the same hole, real mesh",
)

# Vega-Lite has no native "floating inset" - a genuinely nested mini-chart
# isn't supported, so this is a small chart placed beside the main one
# instead: the whole hole (tee to green) with the zoomed region outlined,
# for orientation. Colored by course_area (Rules of Golf classification -
# penalty_area/bunker/putting_green/teeing_area/general_area) rather than
# chart_course()'s default ground_cover, so its legend isn't just a repeat
# of the main chart's ground_cover legend.
whole_hole_course = plotting.chart_course(
    tea_olive.gdf,
    mode="course_area",
    legend=alt.Legend(orient="bottom", direction="vertical"),
)
zoomed_region_outline = alt.Chart(
    gpd.GeoDataFrame(geometry=[region_shell], crs=tea_olive.gdf.crs)
).mark_geoshape(fill=None, stroke="red", strokeWidth=2)


def _compass_rose_paths(*, r_cardinal=32, r_diagonal=19, r_waist=8, w_deg=22.5):
    """
    Build the two SVG path strings for a traditional 8-point compass rose:
    every point is split lengthwise into a black half and a white half
    (the classic pinwheel look), with N/E/S/W longer than the intermediate
    NE/SE/SW/NW points. w_deg=22.5 gives each point the full 45-degree
    sector between it and its neighbors, so adjacent points share an edge
    (no gaps) rather than reading as thin, separated spikes. Bearing 0 (N)
    points toward -y, matching this package's convention of plotting local
    y (true northing) with reflectY=True, so "up" already means north
    without extra rotation.

    Returns: (left_half_path, right_half_path) - two SVG path `d` strings,
    each usable directly as a point mark's `shape`.
    """

    def vertex(bearing_deg, radius):
        theta = np.radians(bearing_deg)
        return radius * np.sin(theta), -radius * np.cos(theta)

    def polygon_path(polygons):
        commands = []
        for polygon in polygons:
            commands.append(f"M{polygon[0][0]:.2f},{polygon[0][1]:.2f}")
            for x, y in polygon[1:]:
                commands.append(f"L{x:.2f},{y:.2f}")
            commands.append("Z")
        return "".join(commands)

    left_halves, right_halves = [], []
    bearings_and_radii = [(b, r_cardinal) for b in (0, 90, 180, 270)] + [
        (b, r_diagonal) for b in (45, 135, 225, 315)
    ]
    for bearing, radius in bearings_and_radii:
        tip = vertex(bearing, radius)
        base_left = vertex(bearing - w_deg, r_waist)
        base_right = vertex(bearing + w_deg, r_waist)
        center = (0.0, 0.0)
        left_halves.append([tip, base_left, center])
        right_halves.append([tip, center, base_right])

    return polygon_path(left_halves), polygon_path(right_halves)


_compass_left, _compass_right = _compass_rose_paths()
compass_xmin, compass_ymin, compass_xmax, compass_ymax = tea_olive.gdf.total_bounds
compass_center = (compass_xmax - 45.0, compass_ymax - 45.0)
compass_location = pd.DataFrame({"x": [compass_center[0]], "y": [compass_center[1]]})
_compass_size = 6.0
compass_rose = alt.Chart(compass_location).mark_point(
    shape=_compass_left, size=_compass_size, filled=True, color="black"
).encode(longitude="x", latitude="y") + alt.Chart(compass_location).mark_point(
    shape=_compass_right, size=_compass_size, filled=True, color="white", stroke="black"
).encode(longitude="x", latitude="y")

_compass_label_radius = 16.0
compass_labels = pd.DataFrame(
    {
        "x": [
            compass_center[0] + dx * _compass_label_radius
            for dx in (0.0, 1.0, 0.0, -1.0)
        ],
        "y": [
            compass_center[1] + dy * _compass_label_radius
            for dy in (1.0, 0.0, -1.0, 0.0)
        ],
        "label": ["N", "E", "S", "W"],
    }
)
compass_rose_labels = alt.Chart(compass_labels).mark_text(
    fontSize=9, fontWeight="bold"
).encode(longitude="x", latitude="y", text="label")

overview_chart = (
    (whole_hole_course + zoomed_region_outline + compass_rose + compass_rose_labels)
    .project(type="identity", reflectY=True)
    .properties(width=220, height=220, title="Hole 1 overview")
)

# Vega-Lite also can't relocate a legend to a different (non-data-bearing)
# view - the main chart's slope_grade/ground_cover/v legends were
# suppressed above (legend=False), and these are small standalone charts
# built purely to host their relocated legends underneath the overview,
# stacked vertically via vconcat.
_legend_common = {"width": 20, "height": 1}
slope_grade_legend = (
    alt.Chart(region_mesh)
    .mark_point(shape="wedge", filled=True, color="DarkViolet")
    .encode(
        longitude="x",
        latitude="y",
        angle="slope_heading",
        size=alt.Size(
            "slope_grade",
            scale=alt.Scale(domain=[0, max_stable_grade], clamp=True),
            legend=alt.Legend(orient="bottom", direction="vertical"),
        ),
    )
    .project(type="identity", reflectY=True)
    .properties(**_legend_common)
)
ground_cover_legend = (
    plotting.chart_course(
        region_course, legend=alt.Legend(orient="bottom", direction="vertical")
    )
    .project(type="identity", reflectY=True)
    .properties(**_legend_common)
)
# Sub-legends stack vertically, but the "v" gradient bar itself stays
# horizontal (short and wide), matching how it's always been drawn.
speed_legend = (
    plotting.chart_trajectories(
        trajectory_dfs,
        legend=alt.Legend(orient="bottom", direction="horizontal"),
    )
    .project(type="identity", reflectY=True)
    .properties(**_legend_common)
)

legend_column = alt.vconcat(
    overview_chart, slope_grade_legend, ground_cover_legend, speed_legend
).resolve_scale(color="independent", size="independent")

layout = alt.hconcat(combined, legend_column).resolve_scale(
    color="independent", size="independent"
)

out_path = pathlib.Path(__file__).resolve().parent / "tea_olive_multi_putt.html"
layout.save(out_path)
print("saved:", out_path)
