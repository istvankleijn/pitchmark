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
