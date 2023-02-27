from pathlib import Path

import pytest

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
