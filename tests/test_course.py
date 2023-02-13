import itertools

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


def test_Course_from_featurecollection(augusta_national):
    handler = pitchmark.osm.GolfHandler()
    handler.apply_file(augusta_national)
    fc = handler.feature_collection
    course = pitchmark.Course.from_featurecollection(fc)
    assert len(course.holes) == 18
