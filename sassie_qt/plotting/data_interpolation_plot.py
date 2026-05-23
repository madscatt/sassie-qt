"""Plotly figure builders for data_interpolation output."""

from __future__ import annotations

import json
from pathlib import Path


def build_data_interpolation_figure(plot_data_file: Path) -> dict:
    """Build the Plotly figure GenApp returned for data_interpolation."""

    with plot_data_file.open() as file_object:
        plot_data = json.load(file_object)

    cutoff_x_value = plot_data["signal_to_noise_cutoff_value"]
    cutoff_y_value = _value_at_x(
        plot_data["original_q"],
        plot_data["original_iq"],
        cutoff_x_value,
    )
    cutoff_y_error_value = plot_data["original_iq"][0] * 0.5

    return {
        "data": [
            {
                "x": plot_data["original_q"],
                "y": plot_data["original_iq"],
                "xaxis": "x",
                "yaxis": "y",
                "error_y": {
                    "type": "data",
                    "array": plot_data["original_iq_error"],
                    "visible": True,
                    "thickness": 1.5,
                    "width": 0,
                },
                "type": "scatter",
                "mode": "markers",
                "name": "original data",
                "marker": {
                    "size": 4.5,
                    "symbol": "circle",
                    "color": "red",
                },
                "hoverinfo": "x+y",
            },
            {
                "x": plot_data["q"],
                "y": plot_data["iq"],
                "xaxis": "x",
                "yaxis": "y",
                "error_y": {
                    "type": "data",
                    "array": plot_data["iq_error"],
                    "visible": True,
                    "thickness": 1.5,
                    "width": 0,
                },
                "type": "scatter",
                "mode": "lines+markers",
                "name": "interpolated data",
                "line": {
                    "dash": "solid",
                    "color": "blue",
                    "width": 2,
                    "shape": "spline",
                },
                "marker": {
                    "color": "blue",
                    "size": 6,
                    "symbol": "circle",
                },
                "hoverinfo": "x+y",
            },
            {
                "x": [cutoff_x_value],
                "y": [cutoff_y_value],
                "xaxis": "x",
                "yaxis": "y",
                "error_y": {
                    "type": "data",
                    "array": [cutoff_y_error_value],
                    "visible": True,
                    "thickness": 2.5,
                    "width": 0,
                },
                "type": "scatter",
                "mode": "lines+markers",
                "name": (
                    "cutoff q value: "
                    + str(cutoff_x_value)
                    + "<br>[I(q)/(std.dev. I(q))] < 2"
                ),
                "marker": {
                    "color": "grey",
                    "size": 2,
                    "symbol": "circle",
                },
                "line": {
                    "dash": "solid",
                    "color": "grey",
                    "width": 3,
                },
                "hoverinfo": "x+y",
            },
        ],
        "layout": {
            "title": {
                "text": "Data Interpolation Plot",
                "y": 0.9,
                "x": 0.47,
            },
            "hovermode": "closest",
            "xaxis": {
                "type": "log",
                "title": "q (A<sup>-1</sup>)",
                "autorange": True,
                "showgrid": True,
                "zeroline": False,
                "showline": True,
                "autotick": True,
                "ticks": "inside",
                "mirror": "ticks",
                "showticklabels": True,
            },
            "yaxis": {
                "type": "log",
                "title": "I(q)",
                "autorange": True,
                "showgrid": True,
                "zeroline": False,
                "showline": True,
                "autotick": True,
                "ticks": "inside",
                "mirror": "ticks",
                "showticklabels": True,
                "exponentformat": "e",
            },
        },
        "config": {
            "responsive": True,
            "scrollZoom": True,
            "toImageButtonOptions": {
                "format": "png",
                "scale": 2,
            },
            "modeBarButtonsToRemove": ["select2d", "lasso2d"],
            "modeBarButtonsToAdd": [
                "togglespikelines",
                "v1hovermode",
                "hovercompare",
            ],
            "displaylogo": False,
        },
    }


def load_data_interpolation_plot_data(plot_data_file: Path) -> dict:
    with plot_data_file.open() as file_object:
        return json.load(file_object)


def export_data_interpolation_plotly_html(
    plot_data_file: Path,
    html_file: Path | None = None,
) -> Path:
    """Write a self-contained Plotly HTML file beside SASSIE module outputs."""

    figure = build_data_interpolation_figure(plot_data_file)
    html_file = html_file or plot_data_file.with_name(
        f"{plot_data_file.stem}_plotly.html"
    )
    html_file.write_text(_plotly_html_document(figure), encoding="utf-8")
    return html_file


def _value_at_x(x_values: list[float], y_values: list[float], x_value: float) -> float:
    if x_value in x_values:
        return y_values[x_values.index(x_value)]

    closest_index = min(
        range(len(x_values)),
        key=lambda index: abs(x_values[index] - x_value),
    )
    return y_values[closest_index]


def _plotly_html_document(figure: dict) -> str:
    return (
        "<!doctype html>"
        "<html>"
        "<head>"
        "<meta charset='utf-8'>"
        "<title>Data Interpolation Plot</title>"
        f"<script>{_plotly_javascript()}</script>"
        "<style>"
        "html, body, #plot { width: 100%; height: 100%; margin: 0; }"
        "body { background: #ffffff; overflow: hidden; }"
        "</style>"
        "</head>"
        "<body>"
        "<div id='plot'></div>"
        "<script>"
        f"const figure = {json.dumps(figure)};"
        "Plotly.newPlot('plot', figure.data || [], figure.layout || {}, figure.config || {});"
        "window.addEventListener('resize', () => Plotly.Plots.resize('plot'));"
        "</script>"
        "</body>"
        "</html>"
    )


def _plotly_javascript() -> str:
    try:
        import plotly
    except ImportError as error:
        raise RuntimeError("The Python plotly package is required for Plotly export.") from error

    plotly_path = Path(plotly.__file__).resolve().parent
    javascript_path = plotly_path / "package_data" / "plotly.min.js"
    if not javascript_path.exists():
        raise RuntimeError(f"Could not find plotly.min.js at {javascript_path}")
    return javascript_path.read_text(encoding="utf-8")
