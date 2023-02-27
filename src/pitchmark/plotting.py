import altair as alt


_palette = {
    "water": "RoyalBlue",
    "sand": "Khaki",
    "green": "Aquamarine",
    "short_grass": "LawnGreen",
    "woods": "ForestGreen",
    "long_grass": "LimeGreen",
}


def chart_course(geodataframe, *, mode="ground_cover", tooltip=True):
    match mode:
        case "ground_cover":
            _domain = list(_palette.keys())
            _range = list(_palette.values())
        case _:
            raise ValueError(f"{mode=} not implemented")

    if tooltip is True:
        tooltip = ["name", "ground_cover", "course_area"]
    elif tooltip in (False, None):
        tooltip = alt.value(None)

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
    )
    return course_chart
