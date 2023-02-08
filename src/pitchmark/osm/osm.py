import json

import osmium


class GolfHandler(osmium.SimpleHandler):
    tags = {
        ("golf", "hole"),
        ("golf", "tee"),
        ("golf", "green"),
        ("golf", "fairway"),
        ("golf", "rough"),
        ("golf", "bunker"),
        ("golf", "water_hazard"),
        ("golf", "lateral_water_hazard"),
        ("natural", "wood"),
    }

    def __init__(self):
        super().__init__()
        self.jsonfab = osmium.geom.GeoJSONFactory()
        self.feature_collection = {"type": "FeatureCollection", "features": []}

    def way(self, w):
        if w.is_closed():
            return
        for key, value in type(self).tags:
            if w.tags.get(key) == value:
                self.add_feature(self.jsonfab.create_linestring(w), w.tags)

    def area(self, a):
        for key, value in type(self).tags:
            if a.tags.get(key) == value:
                self.add_feature(self.jsonfab.create_multipolygon(a), a.tags)

    def add_feature(self, geom_string, tags):
        feature = {
            "type": "Feature",
            "geometry": json.loads(geom_string),
            "properties": dict(tags),
        }
        self.feature_collection["features"].append(feature)
