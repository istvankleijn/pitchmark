from dataclasses import dataclass, field
import json

import shapely

from pitchmark.geom import polygon_from_geojson
from pitchmark.hole import Hole


@dataclass
class Course:
    """A representation of a golf course."""

    holes: list[Hole] = field(default_factory=list)
    greens: list[shapely.Polygon] = field(default_factory=list)
    tees: list[shapely.Polygon] = field(default_factory=list)
    fairways: list[shapely.Polygon] = field(default_factory=list)
    bunkers: list[shapely.Polygon] = field(default_factory=list)
    rough: list[shapely.Polygon] = field(default_factory=list)
    water: list[shapely.Polygon] = field(default_factory=list)
    woods: list[shapely.Polygon] = field(default_factory=list)

    @classmethod
    def from_featurecollection(cls, fc):
        course_dict = dict(fc)
        course = cls()
        for feature in course_dict["features"]:
            geometry = feature["geometry"]
            properties = feature["properties"]
            geom_string = json.dumps(geometry)
            if properties.get("golf") == "hole":
                course.holes.append(
                    (
                        int(properties.get("ref")),
                        properties.get("name"),
                        shapely.from_geojson(geom_string),
                    )
                )
            if properties.get("golf") == "green":
                course.greens.append(polygon_from_geojson(geom_string))
            if properties.get("golf") == "tee":
                course.tees.append(polygon_from_geojson(geom_string))
            if properties.get("golf") == "fairway":
                course.fairways.append(polygon_from_geojson(geom_string))
            if properties.get("golf") == "bunker":
                course.bunkers.append(polygon_from_geojson(geom_string))
            if properties.get("golf") == "rough":
                course.rough.append(polygon_from_geojson(geom_string))
            if properties.get("golf") in ("water_hazard", "lateral_water_hazard"):
                course.water.append(polygon_from_geojson(geom_string))
            if properties.get("natural") == "wood":
                course.woods.append(polygon_from_geojson(geom_string))

        return course
