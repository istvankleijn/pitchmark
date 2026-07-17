from pathlib import Path

import geopandas as gpd
import pytest
import shapely

import pitchmark
import pitchmark.osm


@pytest.fixture
def augusta_national_path():
    return Path(".") / "tests" / "augusta_national.osm"


@pytest.fixture
def augusta_national(augusta_national_path):
    handler = pitchmark.osm.GolfHandler()
    handler.apply_file(augusta_national_path)
    fc = handler.feature_collection
    course = pitchmark.Course.from_featurecollection(fc)
    return course


@pytest.fixture
def azalea(augusta_national):
    return augusta_national.holes[12]


@pytest.fixture
def circle10_polygon():
    centre = shapely.Point(0, 0)
    return shapely.buffer(centre, 10.0)


@pytest.fixture
def circle10_gdf(circle10_polygon):
    return gpd.GeoDataFrame(
        geometry=[circle10_polygon], crs="+proj=tmerc +ellps=WGS84 +units=yd +vunits=yd"
    )
