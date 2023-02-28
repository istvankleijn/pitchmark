import enum

import laspy
import numpy as np
import shapely

from pitchmark.geom import prepared_shell


class LasClassification(enum.IntEnum):
    created_never_classified = 0
    unclassified = 1
    ground = 2
    low_vegetation = 3
    medium_vegetation = 4
    high_vegetation = 5
    building = 6
    low_point = 7
    noise = 7
    model_keypoint = 8
    mass_point = 8
    water = 9


def clip_to_geoseries(
    from_files,
    geoseries,
    *,
    to_file="out.laz",
    classification_filter=None,
    shell_distance=2.0
):
    """
    Read in multiple LAS/LAZ files, filter points with specified classifications,
    clip them to the extent of a specified GeoSeries with an additional buffer,
    and export to a single new file.

    The header is adapted from the first input file. Caution: this assumes that the
    input files are compatible with each other (i.e. using any of their headers should
    give the same result).

    Default classifications: Unclassified and Ground.
    """
    if classification_filter is None:
        classification_filter = [
            LasClassification.unclassified,
            LasClassification.ground,
        ]
    with laspy.open(from_files[0]) as handle:
        export_header = handle.header
    masked_area = prepared_shell(
        geoseries, distance=shell_distance, crs_to=export_header.parse_crs()
    )

    # file by file, extract raw LAS points data (stored in ndarrays), and prepare
    # a list of these arrays that is concatenated before being exported
    export_raw = list()
    for file in from_files:
        dataset = laspy.read(file)
        filtered_data = dataset[np.isin(dataset.classification, classification_filter)]
        contained_in_area = shapely.contains_xy(
            masked_area, filtered_data.x, filtered_data.y
        )
        raw_points_in_area = filtered_data[contained_in_area].points.array
        export_raw.append(raw_points_in_area)
    export_array = np.hstack(export_raw)

    export_data = laspy.LasData(export_header)
    export_data.points = laspy.ScaleAwarePointRecord(
        export_array,
        export_header.point_format,
        export_header.scales,
        export_header.offsets,
    )
    export_data.update_header()

    export_data.write(to_file)
