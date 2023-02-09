import json

import osmium


golf_tags = {
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


class GolfHandler(osmium.SimpleHandler):
    """
    Handler to parse an OpenStreetMap XML file and construct a GeoJSON-like feature
    collection (dictionary) of all its golf-related objects.

    Usage
    -----
    >>> handler = GolfHandler()
    >>> handler.apply_file(map_path, locations=True)
    >>> json.dumps(handler.feature_collection)
    """

    def __init__(self):
        super().__init__()
        self.jsonfab = osmium.geom.GeoJSONFactory()
        self.feature_collection = {"type": "FeatureCollection", "features": []}

    def way(self, w):
        if w.is_closed():
            return
        self.add_feature(w, "linestring")

    def area(self, a):
        self.add_feature(a, "multipolygon")

    def add_feature(self, obj, geom_type):
        match geom_type:
            case "linestring":
                factory_method = self.jsonfab.create_linestring
            case "multipolygon":
                factory_method = self.jsonfab.create_multipolygon
            case _:
                raise ValueError(f"{geom_type=} not supported")
        geom_string = factory_method(obj)
        for key, value in golf_tags:
            if obj.tags.get(key) == value:
                geom_string = factory_method(obj)
                feature = {
                    "type": "Feature",
                    "geometry": json.loads(geom_string),
                    "properties": dict(obj.tags),
                }
                self.feature_collection["features"].append(feature)
