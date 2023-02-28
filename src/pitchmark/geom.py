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
