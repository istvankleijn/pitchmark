from dataclasses import dataclass, field
import itertools
import json
import operator
import warnings

import geopandas as gpd
import pandas as pd
import shapely

from pitchmark.geom import polygon_from_geojson
from pitchmark.hole import Hole
from pitchmark.plotting import chart_course


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
    proj_string: str | None = field(init=False)
    gdf: gpd.GeoDataFrame = field(init=False)

    def __post_init__(self):
        self.holes.sort(key=operator.attrgetter("hole_number"))
        # transverse Mercator centered on 1st tee with WGS84 datum, in yards
        try:
            lon_0, lat_0 = self.holes[0].path.coords[0]
            self.proj_string = f"+proj=tmerc +{lon_0=} +{lat_0=} +ellps=WGS84 +units=yd"
        except IndexError:
            warnings.warn(
                "No first tee present, could not construct projection string."
            )
            self.proj_string = None
        data = {
            "name": pd.Categorical(
                [
                    "water_hazard",
                    "bunkers",
                    "green",
                    "tee",
                    "fairway",
                    "woods",
                    "rough",
                ],
            ),
            "course_area": pd.Categorical(
                [
                    "penalty_area",
                    "bunker",
                    "putting_green",
                    "teeing_area",
                    "general_area",
                    "general_area",
                    "general_area",
                ],
                categories=[
                    "penalty_area",
                    "bunker",
                    "putting_green",
                    "teeing_area",
                    "general_area",
                ],
                ordered=True,
            ),
            "ground_cover": pd.Categorical(
                [
                    "water",
                    "sand",
                    "green",
                    "short_grass",
                    "short_grass",
                    "woods",
                    "long_grass",
                ],
                categories=[
                    "water",
                    "sand",
                    "green",
                    "short_grass",
                    "woods",
                    "long_grass",
                ],
                ordered=True,
            ),
        }
        course_gdf = gpd.GeoDataFrame(
            data,
            geometry=[
                shapely.MultiPolygon(x)
                for x in [
                    self.water,
                    self.bunkers,
                    self.greens,
                    self.tees,
                    self.fairways,
                    self.woods,
                    self.rough,
                ]
            ],
            crs="EPSG:4326",  # WGS84 in longitude/latitude (degrees)
        )
        if self.proj_string is not None:
            self.gdf = course_gdf.to_crs(self.proj_string)
        else:
            self.gdf = course_gdf

    @classmethod
    def from_featurecollection(cls, fc):
        course_dict = dict(fc)
        holes, greens, tees, fairways, bunkers, rough, water, woods = [
            [] for _ in range(8)
        ]
        for feature in course_dict["features"]:
            geometry = feature["geometry"]
            properties = feature["properties"]
            geom_string = json.dumps(geometry)
            if properties.get("golf") == "hole":
                holes.append(
                    Hole(
                        int(properties.get("ref")),
                        properties.get("name"),
                        shapely.from_geojson(geom_string),
                    )
                )
            if properties.get("golf") == "green":
                greens.append(polygon_from_geojson(geom_string))
            if properties.get("golf") == "tee":
                tees.append(polygon_from_geojson(geom_string))
            if properties.get("golf") == "fairway":
                fairways.append(polygon_from_geojson(geom_string))
            if properties.get("golf") == "bunker":
                bunkers.append(polygon_from_geojson(geom_string))
            if properties.get("golf") == "rough":
                rough.append(polygon_from_geojson(geom_string))
            if properties.get("golf") in ("water_hazard", "lateral_water_hazard"):
                water.append(polygon_from_geojson(geom_string))
            if properties.get("natural") == "wood":
                woods.append(polygon_from_geojson(geom_string))

        return cls(holes, greens, tees, fairways, bunkers, rough, water, woods)

    def chart(self):
        return chart_course(self.gdf)
