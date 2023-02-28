"""A subpackage for parsing LiDar files."""

# read version from installed package
from importlib.metadata import version

__version__ = version("pitchmark")

# Populate namespace
from pitchmark.lidar import las
