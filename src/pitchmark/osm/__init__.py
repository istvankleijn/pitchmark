"""A subpackage for parsing OpenStreetMap files."""

# read version from installed package
from importlib.metadata import version

__version__ = version("pitchmark")

from pitchmark.osm.osm import golf_tags, GolfHandler
