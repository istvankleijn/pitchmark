import altair as alt
import pytest

import pitchmark.plotting


@pytest.mark.parametrize(
    "mode, tooltip",
    [
        ("ground_cover", True),
        ("ground_cover", False),
        ("ground_cover", None),
        ("course_area", True),
    ],
)
def test_chart_course(augusta_national, mode, tooltip):
    gdf = augusta_national.gdf
    if mode != "ground_cover":
        with pytest.raises(ValueError, match=f"{mode=} not implemented"):
            chart = pitchmark.plotting.chart_course(gdf, mode=mode)
        return

    chart = pitchmark.plotting.chart_course(gdf, mode=mode, tooltip=tooltip)
    assert isinstance(chart, alt.Chart)

    chart_dict = chart.to_dict()
    assert chart_dict["mark"] == "geoshape"
    assert chart_dict["encoding"]["color"]["field"] == mode
    if tooltip is True:
        assert chart_dict["encoding"]["tooltip"] == [
            {"field": "name", "type": "nominal"},
            {"field": "ground_cover", "type": "nominal"},
            {"field": "course_area", "type": "nominal"},
        ]
