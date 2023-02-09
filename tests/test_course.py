import itertools

import pytest

import pitchmark
import pitchmark.osm

from fixtures import augusta_national


@pytest.mark.parametrize(
    "holes, greens, tees, fairways, bunkers, rough, water, woods",
    [
        tuple(itertools.repeat(None, 8)),
    ],
)
def test_Course(holes, greens, tees, fairways, bunkers, rough, water, woods):
    course = pitchmark.Course(
        holes, greens, tees, fairways, bunkers, rough, water, woods
    )
    if holes is None:
        holes = list()
    if greens is None:
        greens = list()
    if tees is None:
        tees = list()
    if fairways is None:
        fairways = list()
    if bunkers is None:
        bunkers = list()
    if rough is None:
        rough = list()
    if water is None:
        water = list()
    if woods is None:
        woods = list()
    assert course.holes == holes
    assert course.greens == greens
    assert course.tees == tees
    assert course.fairways == fairways
    assert course.bunkers == bunkers
    assert course.rough == rough
    assert course.water == water
    assert course.woods == woods


def test_Course_from_featurecollection(augusta_national):
    handler = pitchmark.osm.GolfHandler()
    handler.apply_file(augusta_national)
    fc = handler.feature_collection
    course = pitchmark.Course.from_featurecollection(fc)
    assert len(course.holes) == 18
