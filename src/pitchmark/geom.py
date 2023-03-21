import geopandas as gpd
import numpy as np
import open3d as o3d
import pyproj
import shapely


def polygon_from_geojson(geom_string):
    multipolygon = shapely.from_geojson(geom_string)
    geoms = multipolygon.geoms
    if len(geoms) != 1:
        raise ValueError(
            "MultiPolygon must contain exactly one polygon for lossless unpacking"
        )
    polygon = geoms[0]
    return polygon


def prepared_shell(geoseries, *, distance=0.0, crs_to=None):
    """
    Construct a shell (buffer) around the (unary union of the) geometries in a given
    Geoseries, optionally transform it to a different CRS, and prepare it to improve
    computational efficiency of subsequent operations.
    """
    masked_area = geoseries.unary_union.buffer(distance)

    if crs_to is not None:
        transformer = pyproj.Transformer.from_crs(geoseries.crs, crs_to, always_xy=True)
        masked_area = shapely.ops.transform(transformer.transform, masked_area)

    shapely.prepare(masked_area)
    return masked_area


def delaunay3d(xyz, *, transformer=None, shell=None):
    """
    Construct 2.5D Delaunay triangulation from an X, Y, Z array of 3D point cloud data,
    and optionally project to a different CRS and/or remove triangles outside a
    predefined shell.

    Parameters:
    xyz: np.array
        Point cloud data.
    transformer: pyproj.Transformer or None, default None
    shell: shapely.Polygon or None, default None
        For best results, the shell should be prepared before calling this function.
    """
    if transformer is not None:
        xyz = np.array(list(transformer.itransform(xyz)))
    points = shapely.MultiPoint(xyz)
    dt = shapely.delaunay_triangles(points)
    if shell is None:
        return dt
    triangles = [t for t in dt.geoms if t.within(shell)]
    return triangles


def simplify_close_vertices(mesh, distance=0.001):
    """
    Simplify an Open3D TriangleMesh by merging close vertices and removing residual
    geometries.
    """
    mesh.merge_close_vertices(distance)
    mesh.remove_degenerate_triangles()
    mesh.remove_unreferenced_vertices()


def simplified_mesh(triangles, *, merge_close=0.25, smooth_iters=10):
    """
    Construct an Open3D mesh defined by a sequence of 2.5D shapely triangles, merge
    close vertices and smoothen out the surface.
    """
    vertices = o3d.utility.Vector3dVector(
        np.array([triangle.exterior.coords[:-1] for triangle in triangles]).reshape(
            (-1, 3)
        )
    )
    triangle_indices = o3d.utility.Vector3iVector(
        np.arange(len(vertices)).reshape((-1, 3))
    )
    mesh = o3d.geometry.TriangleMesh(vertices, triangle_indices)
    simplify_close_vertices(mesh, merge_close)
    for _ in range(smooth_iters):
        mesh = mesh.filter_smooth_taubin()
        simplify_close_vertices(mesh, merge_close)
    return mesh


def gdf_from_mesh(mesh, crs=None):
    """
    Construct a GeoDataFrame from an Open3D TriangleMesh.
    """
    triangles = shapely.polygons(np.asarray(mesh.vertices)[np.asarray(mesh.triangles)])
    mesh.compute_triangle_normals()
    normals = np.asarray(mesh.triangle_normals)
    centroids = np.array(
        [sum(np.array(triangle.exterior.coords[:-1])) / 3 for triangle in triangles]
    )
    gdf = gpd.GeoDataFrame(geometry=triangles, crs=crs)
    gdf[["x", "y", "z"]] = centroids
    gdf[["normal_x", "normal_y", "normal_z"]] = normals
    gdf["slope_heading"] = np.degrees(np.arctan2(gdf["normal_x"], gdf["normal_y"]))
    gdf["slope_heading"] = np.where(
        gdf["slope_heading"] < 0, gdf["slope_heading"] + 360, gdf["slope_heading"]
    )
    gdf["slope_grade"] = 100.0 * np.sqrt(1.0 - gdf["normal_z"] ** 2)
    return gdf
