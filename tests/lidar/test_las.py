import geopandas as gpd
import laspy
import numpy as np
import pyproj
import shapely

import pitchmark.lidar.las as las_mod

# GROUND_CRS (geographic) and GEOSERIES_CRS (its UTM zone) share the same
# WGS84 datum, so reprojecting between them is a direct forward/inverse map
# projection with no datum transform (and thus no external grid shift file,
# unlike e.g. WGS84<->OSGB36) - deterministic and portable across machines/CI.
GROUND_CRS = pyproj.CRS.from_epsg(4326)
GEOSERIES_CRS = pyproj.CRS.from_epsg(32630)

# An arbitrary real-world point, used as a shared origin, expressed in each CRS.
_ORIGIN_LONLAT = (-2.8070, 56.3432)
_ORIGIN_UTM = pyproj.Transformer.from_crs(
    GROUND_CRS, GEOSERIES_CRS, always_xy=True
).transform(*_ORIGIN_LONLAT)
_GEOD = pyproj.Geod(ellps="WGS84")


def _offset_lonlat(dx, dy):
    """(lon, lat) of the point dx metres east and dy metres north of the origin."""
    distance = (dx**2 + dy**2) ** 0.5
    if distance == 0:
        return _ORIGIN_LONLAT
    azimuth = np.degrees(np.arctan2(dx, dy))
    lon, lat, _ = _GEOD.fwd(*_ORIGIN_LONLAT, azimuth, distance)
    return lon, lat


def _write_las(path, points):
    """
    Write a minimal synthetic LAS file in GROUND_CRS.

    points: sequence of (dx, dy, z, classification) tuples, dx/dy given as
    metres east/north of the origin (converted to lon/lat internally, since
    GROUND_CRS is geographic).
    """
    lonlats = [_offset_lonlat(dx, dy) for dx, dy, _, _ in points]
    xs = [lonlat[0] for lonlat in lonlats]
    ys = [lonlat[1] for lonlat in lonlats]
    zs = [point[2] for point in points]
    classes = [point[3] for point in points]

    header = laspy.LasHeader(point_format=2, version="1.2")
    header.add_crs(GROUND_CRS)
    # A metre-scale increment (as used for a projected CRS) would round every
    # coordinate to the nearest ~0.001 degree (over 100m) here - GROUND_CRS is
    # geographic, so the scale needs to resolve sub-metre degree fractions.
    header.scales = [1e-9, 1e-9, 0.001]
    header.offsets = [_ORIGIN_LONLAT[0], _ORIGIN_LONLAT[1], 0.0]
    las = laspy.LasData(header)
    las.x = np.array(xs, dtype=float)
    las.y = np.array(ys, dtype=float)
    las.z = np.array(zs, dtype=float)
    las.classification = np.array(classes)
    las.write(path)
    return path


def _geoseries(*, buffer=20.0):
    """A circle of the given radius (metres) around the origin, in GEOSERIES_CRS."""
    return gpd.GeoSeries(
        [shapely.Point(*_ORIGIN_UTM).buffer(buffer)], crs=GEOSERIES_CRS
    )


def test_clip_to_geoseries_filters_by_classification_and_distance(tmp_path):
    points = [
        (5, 0, 1.0, las_mod.LasClassification.ground),  # inside, ground -> keep
        (-5, 0, 2.0, las_mod.LasClassification.ground),  # inside, ground -> keep
        (0, 5, 3.0, las_mod.LasClassification.high_vegetation),  # inside, filtered
        (50, 0, 4.0, las_mod.LasClassification.ground),  # outside -> filtered
        (0, 0, 5.0, las_mod.LasClassification.unclassified),  # inside -> keep
    ]
    from_file = _write_las(tmp_path / "in.las", points)
    to_file = tmp_path / "out.las"

    las_mod.clip_to_geoseries(
        [from_file], _geoseries(), to_file=to_file, shell_distance=5.0
    )

    result = laspy.read(to_file)
    assert sorted(result.z) == [1.0, 2.0, 5.0]
    assert result.header.parse_crs().to_epsg() == GROUND_CRS.to_epsg()


def test_clip_to_geoseries_custom_classification_filter(tmp_path):
    points = [
        (5, 0, 1.0, las_mod.LasClassification.ground),
        (0, 0, 2.0, las_mod.LasClassification.unclassified),
    ]
    from_file = _write_las(tmp_path / "in.las", points)
    to_file = tmp_path / "out.las"

    las_mod.clip_to_geoseries(
        [from_file],
        _geoseries(),
        to_file=to_file,
        shell_distance=5.0,
        classification_filter=[las_mod.LasClassification.ground],
    )

    result = laspy.read(to_file)
    assert list(result.z) == [1.0]


def test_clip_to_geoseries_concatenates_multiple_files(tmp_path):
    file_a = _write_las(
        tmp_path / "a.las",
        [
            (5, 0, 1.0, las_mod.LasClassification.ground),  # keep
            (50, 0, 9.0, las_mod.LasClassification.ground),  # filtered by distance
        ],
    )
    file_b = _write_las(
        tmp_path / "b.las",
        [
            (-5, 0, 2.0, las_mod.LasClassification.ground),  # keep
            (0, 0, 3.0, las_mod.LasClassification.unclassified),  # keep
        ],
    )
    to_file = tmp_path / "out.las"

    las_mod.clip_to_geoseries(
        [file_a, file_b], _geoseries(), to_file=to_file, shell_distance=5.0
    )

    result = laspy.read(to_file)
    # order preserved: file_a's surviving points first, then file_b's
    assert list(result.z) == [1.0, 2.0, 3.0]
