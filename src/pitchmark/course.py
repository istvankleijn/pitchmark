from dataclasses import dataclass, field
import json
import operator
import warnings

import geopandas as gpd
import pandas as pd
import pyproj
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
    transformer_to_local: pyproj.Transformer | None = field(init=False, repr=False)
    gdf: gpd.GeoDataFrame = field(init=False, repr=False)

    def __post_init__(self):
        self.holes.sort(key=operator.attrgetter("hole_number"))
        # transverse Mercator centered on 1st tee with WGS84 datum, in yards
        try:
            lon_0, lat_0 = self.holes[0].path.coords[0]
            self.proj_string = f"+proj=tmerc +{lon_0=} +{lat_0=} +ellps=WGS84 +units=yd"
            self.transformer_to_local = pyproj.Transformer.from_crs(
                "EPSG:4326", self.proj_string, always_xy=True
            )
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
        ).explode(ignore_index=True)
        if self.proj_string is not None:
            self.gdf = course_gdf.to_crs(self.proj_string)
            self.populate_hole_gdfs()
            self.trim_to_features_in_play()
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

    def chart(self, **kwargs):
        return chart_course(self.gdf, **kwargs).configure_legend(disable=True)

    def mask_hole(
        self,
        hole_path,
        *,
        tee_buffer=10.0,
        fairway_buffer=20.0,
        green_buffer=30.0,
        approach_buffer=50.0,
    ):
        fairways = self.gdf[
            (self.gdf.name == "fairway")
            & (self.gdf["geometry"].apply(shapely.intersects, args=(hole_path,)))
        ]
        green = self.gdf[
            (self.gdf.name == "green")
            & (self.gdf["geometry"].apply(shapely.intersects, args=(hole_path,)))
        ]
        shot_locations = [shapely.Point(hole_path.coords[0]).buffer(tee_buffer)] + [
            shapely.buffer(shapely.Point(x), approach_buffer)
            for x in hole_path.coords[1:]
        ]
        shot_connectors = []
        for x, y in zip(shot_locations[:-1], shot_locations[1:]):
            mp = shapely.MultiPolygon([x, y])
            shot_connectors.append(mp.convex_hull)
        shots_envelope = shapely.unary_union(shot_connectors)
        mask = shapely.unary_union(
            (
                fairways.unary_union.buffer(fairway_buffer),
                green.unary_union.buffer(green_buffer),
                shots_envelope,
            )
        )
        return mask

    def populate_hole_gdfs(self, **kwargs):
        for hole in self.holes:
            hole_path = shapely.ops.transform(
                self.transformer_to_local.transform, hole.path
            )
            mask = self.mask_hole(hole_path, **kwargs)
            hole.gdf = self.gdf.clip(mask)

    def trim_to_features_in_play(self):
        indices_in_play = pd.concat(
            [hole.gdf for hole in self.holes],
        ).index.unique()
        in_play = self.gdf.iloc[indices_in_play]
        self.gdf = in_play
