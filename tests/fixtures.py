from pathlib import Path

import pytest


@pytest.fixture
def augusta_national():
    return Path(".") / "tests" / "augusta_national.osm"
