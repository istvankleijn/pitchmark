"""A subpackage for parsing OpenStreetMap files."""

# read version from installed package
from importlib.metadata import version

__version__ = version("pitchmark")

# Populate namespace
from pitchmark.osm.osm import GolfHandler, golf_tags
