import json

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
