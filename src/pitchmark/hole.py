from dataclasses import dataclass

import shapely


@dataclass
class Hole:
    """A representation of a golf hole."""

    hole_number: int
    name: str = ""
    path: shapely.LineString | None = None
