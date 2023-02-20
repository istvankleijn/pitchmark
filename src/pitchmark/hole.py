from dataclasses import dataclass, field

import geopandas as gpd
import shapely

from pitchmark.plotting import chart_course


@dataclass
class Hole:
    """A representation of a golf hole."""

    hole_number: int
    name: str = ""
    path: shapely.LineString | None = None
    gdf: gpd.GeoDataFrame | None = field(default=None, repr=False)

    def chart(self, **kwargs):
        return (
            chart_course(self.gdf, **kwargs)
            .properties(title=f"{self.hole_number} - {self.name}")
            .configure_legend(disable=True)
        )
