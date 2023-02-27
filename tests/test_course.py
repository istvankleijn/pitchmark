import itertools

import altair as alt
import geopandas as gpd
import pytest

import pitchmark
import pitchmark.osm


@pytest.mark.parametrize(
    "args",
    [
        (),
        (list(),),
        (itertools.repeat(list(), 8)),
    ],
)
def test_Course_init(args):
    course = pitchmark.Course(*args)
    for area in (
        course.holes,
        course.greens,
        course.tees,
        course.fairways,
        course.bunkers,
        course.rough,
        course.water,
        course.woods,
    ):
        print(type(area))
        assert isinstance(area, list)
    assert course.proj_string is None


def test_Course_from_featurecollection(augusta_national_path):
    handler = pitchmark.osm.GolfHandler()
    handler.apply_file(augusta_national_path)
    fc = handler.feature_collection
    course = pitchmark.Course.from_featurecollection(fc)
    assert len(course.holes) == 18
    lon_0, lat_0 = course.holes[0].path.coords[0]
    assert (
        course.proj_string == f"+proj=tmerc +{lon_0=} +{lat_0=} +ellps=WGS84 +units=yd"
    )
    assert isinstance(course.gdf, gpd.GeoDataFrame)
    assert len(course.gdf) == 205
    azalea = course.holes[12]
    assert isinstance(azalea.gdf, gpd.GeoDataFrame)


def test_Course_chart(augusta_national):
    chart = augusta_national.chart()
    assert isinstance(chart, alt.Chart)
