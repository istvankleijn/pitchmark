import altair as alt


def chart_course(geodataframe, *, mode="ground_cover", tooltip=True):
    match mode:
        case "ground_cover":
            _domain = ["water", "sand", "green", "short_grass", "woods", "long_grass"]
            _range = [
                "RoyalBlue",
                "Khaki",
                "PaleGreen",
                "Chartreuse",
                "ForestGreen",
                "LimeGreen",
            ]
        case _:
            raise ValueError(f"{mode=} not implemented")

    if tooltip is True:
        tooltip = ["name", "ground_cover", "course_area"]

    course_chart = (
        alt.Chart(geodataframe.sort_values(by=mode, ascending=False))
        .mark_geoshape()
        .encode(
            color=alt.Color(
                mode,
                scale=alt.Scale(
                    domain=_domain,
                    range=_range,
                ),
            ),
            tooltip=tooltip,
        )
        .project(type="identity", reflectY=True)
        .configure_legend(disable=True)
    )
    return course_chart
