"""A subpackage for simulating golf shot physics."""

# read version from installed package
from importlib.metadata import version

__version__ = version("pitchmark")

# Populate namespace
from pitchmark.physics.rolling import softness, Surface, Green
