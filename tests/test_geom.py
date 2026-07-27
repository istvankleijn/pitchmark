import json

import numpy as np
import open3d as o3d
import pytest
import shapely

import pitchmark


@pytest.mark.parametrize(
    "type, coordinates",
    [
        (
            "MultiPolygon",
            [
                [
                    [[0, 0], [1, 0], [1, 1], [0, 0]],
                ],
            ],
        ),
        (
            "MultiPolygon",
            [
                [
                    [[0, 0], [1, 0], [1, 1], [0, 0]],
                ],
                [
                    [[2, 2], [3, 2], [3, 3], [2, 2]],
                ],
            ],
        ),
    ],
)
def test_polygon_from_geojson(type, coordinates):
    d = {"type": type, "coordinates": coordinates}
    geom_string = json.dumps(d)
    if len(coordinates) != 1:
        with pytest.raises(
            ValueError, match="MultiPolygon must contain exactly one polygon"
        ):
            polygon = pitchmark.geom.polygon_from_geojson(geom_string)
        return
    polygon = pitchmark.geom.polygon_from_geojson(geom_string)
    assert isinstance(polygon, shapely.Polygon)


def _triangle(corners):
    """Build a 2.5D shapely triangle (Polygon with z) from 3 (x, y, z) corners."""
    return shapely.Polygon(list(corners) + [corners[0]])


def test_simplify_close_vertices():
    # Two triangles sharing an edge, built with duplicated (not deduplicated)
    # vertices at the shared corners, as simplified_mesh() constructs them.
    vertices = o3d.utility.Vector3dVector(
        [
            [0, 0, 0],
            [1, 0, 0],
            [1, 1, 0],
            [1, 1, 0],
            [0, 1, 0],
            [0, 0, 0],
        ]
    )
    triangle_indices = o3d.utility.Vector3iVector([[0, 1, 2], [3, 4, 5]])
    mesh = o3d.geometry.TriangleMesh(vertices, triangle_indices)

    pitchmark.geom.simplify_close_vertices(mesh, distance=0.001)

    assert len(mesh.vertices) == 4
    assert len(mesh.triangles) == 2


def test_simplified_mesh():
    triangles = [
        _triangle([(0, 0, 0), (1, 0, 0), (1, 1, 0)]),
        _triangle([(1, 1, 0), (0, 1, 0), (0, 0, 0)]),
    ]

    mesh = pitchmark.geom.simplified_mesh(triangles, merge_close=0.25, smooth_iters=1)

    assert isinstance(mesh, o3d.geometry.TriangleMesh)
    assert len(mesh.triangles) == 2
    # merge_close should collapse the duplicated shared-edge vertices; smoothing
    # a flat, boundary-only mesh shouldn't create any new coincident vertices.
    assert len(mesh.vertices) <= 4


def test_gdf_from_mesh():
    # A single triangle tilted in y-z, so its normal (and therefore slope
    # heading/grade) is known ahead of time.
    vertices = o3d.utility.Vector3dVector([[0, 0, 0], [1, 0, 0], [0, 1, 1]])
    triangle_indices = o3d.utility.Vector3iVector([[0, 1, 2]])
    mesh = o3d.geometry.TriangleMesh(vertices, triangle_indices)

    gdf = pitchmark.geom.gdf_from_mesh(mesh)

    assert len(gdf) == 1
    row = gdf.iloc[0]
    assert row[["x", "y", "z"]].to_numpy() == pytest.approx([1 / 3, 1 / 3, 1 / 3])
    assert row["slope_heading"] == pytest.approx(180.0)
    assert row["slope_grade"] == pytest.approx(100 * np.sqrt(0.5))
