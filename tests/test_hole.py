import altair as alt
import pytest
import shapely

import pitchmark


@pytest.mark.parametrize(
    "args",
    [
        tuple(),
        (1,),
        (2, "Azalea"),
        (3, "Azalea", shapely.LineString([[0, 0], [0, 250], [50, 350]])),
    ],
)
def test_Hole_init(args):
    try:
        hole_number = args[0]
        hole = pitchmark.Hole(*args)
        assert hole.hole_number == hole_number
    except IndexError:
        with pytest.raises(TypeError, match="required positional argument"):
            hole = pitchmark.Hole(*args)
        hole = pitchmark.Hole(0)

    assert hole.gdf is None
    try:
        name = args[1]
    except IndexError:
        name = ""
    assert hole.name == name
    try:
        path = args[2]
    except IndexError:
        path = None
    assert hole.path == path


def test_Hole_chart(azalea):
    chart = azalea.chart()
    assert isinstance(chart, alt.Chart)
