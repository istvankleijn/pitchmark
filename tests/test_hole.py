import pytest
import shapely

import pitchmark


@pytest.mark.parametrize(
    "hole_number, name, path",
    [
        (None, None, None),
        (1, None, None),
        (2, "Azalea", None),
        (3, "Azalea", shapely.LineString([[0, 0], [0, 250], [50, 350]])),
    ],
)
def test_Hole(hole_number, name, path):
    hole = pitchmark.Hole(hole_number, name, path)
    if name is None:
        name = ""
    assert hole.hole_number == hole_number
    assert hole.name == name
    assert hole.path == path
