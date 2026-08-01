"""Chart palette and Altair helpers shared by every page.

The categorical order below is validated for colour-vision deficiency on the
adjacent-pair list (worst adjacent CVD ΔE 9.1, normal-vision ΔE 19.6 against
the light surface ``#fcfcfb``). Three slots — aqua, yellow and magenta — sit
below 3:1 contrast on that surface, so every chart here ships **direct value
labels and a table view**; identity is never carried by hue alone.

The app pins Streamlit to the light theme in ``.streamlit/config.toml`` so
these validated light-surface values are the ones that actually render.
"""

from __future__ import annotations

import altair as alt
import pandas as pd

__all__ = [
    "SERIES",
    "SEQUENTIAL",
    "INK",
    "categorical_scale",
    "base_chart",
    "bar_with_labels",
    "empty_note",
]

#: Categorical slots, in the fixed validated order. Never cycled — a ninth
#: series folds into "Other" or becomes a small multiple.
SERIES = [
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
]

#: Single-hue ramp for magnitude (heatmaps), light to dark.
SEQUENTIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

INK = {
    "surface": "#fcfcfb",
    "primary": "#0b0b0b",
    "secondary": "#52514e",
    "muted": "#898781",
    "grid": "#e1e0d9",
    "axis": "#c3c2b7",
}

#: Stable colour per combination method, so filtering never repaints survivors.
METHOD_ORDER = ["ORIG", "NAIVE", "AVERAGE", "FULL", "PREC", "CONF", "VOTES", "PVC"]


def categorical_scale(domain: list[str] | None = None) -> alt.Scale:
    """Return a colour scale that binds hues to entities, not to rank.

    Args:
        domain: Explicit category order. Defaults to the combination methods.

    Returns:
        An Altair scale with a fixed domain-to-range mapping.
    """
    domain = list(domain) if domain else METHOD_ORDER
    return alt.Scale(domain=domain, range=SERIES[: len(domain)])


def base_chart(data: pd.DataFrame, height: int = 320) -> alt.Chart:
    """Start a chart with recessive chrome and the app's ink colours."""
    return (
        alt.Chart(data)
        .properties(height=height)
        .configure_view(strokeWidth=0, fill=INK["surface"])
        .configure_axis(
            grid=True,
            gridColor=INK["grid"],
            gridWidth=1,
            domainColor=INK["axis"],
            tickColor=INK["axis"],
            labelColor=INK["secondary"],
            titleColor=INK["secondary"],
            labelFontSize=11,
            titleFontSize=11,
            titleFontWeight="normal",
        )
        .configure_legend(
            labelColor=INK["secondary"],
            titleColor=INK["secondary"],
            labelFontSize=11,
            titleFontSize=11,
            symbolType="square",
        )
    )


def bar_with_labels(
    data: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    color_domain: list[str] | None = None,
    x_title: str = "",
    y_title: str = "",
    height: int = 320,
    label_format: str = ".2f",
    tooltip: list[str] | None = None,
) -> alt.LayerChart:
    """A bar chart with direct value labels and a hover tooltip.

    Direct labels are not decoration here — they are the relief the palette
    validation requires for the low-contrast slots.

    Args:
        data: Source rows.
        x: Nominal field for the category axis.
        y: Quantitative field for the value axis.
        color: Field driving hue; ``None`` uses a single blue.
        color_domain: Fixed category order for stable colour assignment.
        x_title: Category axis title.
        y_title: Value axis title.
        height: Chart height in pixels.
        label_format: d3 format string for the direct labels.
        tooltip: Fields to show on hover; defaults to ``x`` and ``y``.

    Returns:
        A layered chart of bars plus labels.
    """
    tooltip_fields = tooltip or [x, y]

    encoding = {
        "x": alt.X(f"{x}:N", title=x_title, sort=None, axis=alt.Axis(labelAngle=0)),
        "y": alt.Y(f"{y}:Q", title=y_title),
        "tooltip": [alt.Tooltip(field) for field in tooltip_fields],
    }
    if color:
        encoding["color"] = alt.Color(
            f"{color}:N",
            scale=categorical_scale(color_domain),
            legend=alt.Legend(title=None, orient="top"),
        )

    bars = alt.Chart(data).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=28).encode(**encoding)

    labels = (
        alt.Chart(data)
        .mark_text(dy=-7, fontSize=10, color=INK["secondary"])
        .encode(
            x=alt.X(f"{x}:N", sort=None),
            y=alt.Y(f"{y}:Q"),
            text=alt.Text(f"{y}:Q", format=label_format),
        )
    )

    return (
        (bars + labels)
        .properties(height=height)
        .configure_view(strokeWidth=0, fill=INK["surface"])
        .configure_axis(
            gridColor=INK["grid"],
            domainColor=INK["axis"],
            tickColor=INK["axis"],
            labelColor=INK["secondary"],
            titleColor=INK["secondary"],
            labelFontSize=11,
            titleFontSize=11,
            titleFontWeight="normal",
        )
        .configure_legend(
            labelColor=INK["secondary"],
            titleColor=INK["secondary"],
            labelFontSize=11,
            symbolType="square",
        )
    )


def empty_note(message: str) -> str:
    """Render a muted placeholder for an empty selection."""
    return f"<p style='color:{INK['muted']};font-size:0.9rem;margin:1rem 0'>{message}</p>"
