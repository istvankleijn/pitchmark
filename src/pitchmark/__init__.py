"""A package for exploring golf shot strategy."""

# read version from installed package
from importlib.metadata import version

__version__ = version("pitchmark")


# populate package namespace
from pitchmark import course, geom, hole
