from pathlib import Path

import osmium

import pitchmark.osm

from fixtures import augusta_national


def test_GolfHandler_init():
    handler = pitchmark.osm.GolfHandler()
    assert isinstance(handler, osmium.SimpleHandler)
    assert isinstance(handler.jsonfab, osmium.geom.GeoJSONFactory)
    assert handler.feature_collection == {"type": "FeatureCollection", "features": []}


def test_GolfHandler_usage(augusta_national):
    handler = pitchmark.osm.GolfHandler()
    handler.apply_file(augusta_national)
    features = handler.feature_collection["features"]
    assert len(features) == 248
    azalea = None
    for feature in features:
        assert feature.get("type") == "Feature"
        assert "coordinates" in feature.get("geometry")
        properties = feature.get("properties")
        if properties.get("golf") == "hole" and properties.get("name") == "Azalea":
            azalea = feature
    assert azalea is not None
