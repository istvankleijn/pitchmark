import geopandas as gpd
import pytest

import pitchmark.physics as physics


def test_softness():
    assert physics.softness(6.0) == pytest.approx(0.039815589)
    assert physics.softness(10.0) == pytest.approx(0.023889353)


@pytest.mark.parametrize(
    "stimp, gdf",
    [
        (6.0, None),
        (6.0, gpd.GeoDataFrame()),
    ],
)
def test_Surface_init(stimp, gdf):
    surf = physics.Surface(stimp, gdf=gdf)
    assert isinstance(surf, physics.Surface)
    assert isinstance(surf.gdf, gpd.GeoDataFrame)
    assert surf.stimp == stimp
    assert surf.softness == physics.softness(stimp)


def test_Surface_usage(circle10_gdf):
    stimp = 6.0
    surface = physics.Surface(stimp, circle10_gdf)
    assert surface.normal(1, 1)


def test_MinBallSpeed_init():
    pass


def test_MinBallSpeed_usage():
    pass


def test_Green_init():
    pass


def test_Green_usage():
    pass
