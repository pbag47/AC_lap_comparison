
import pandas
import plotly

from coordinates_handler import Section, dx, dy


def filter_data(section, selected_lap, data) -> pandas.DataFrame:
    driver = selected_lap["Driver"]
    lap = selected_lap["Lap"]
    filtered_data = data[
        (data["Driver"] == driver)
        & (data["Lap Number"] == lap)
        & (data["Car Pos Norm"] > section.start)
        & (data["Car Pos Norm"] < section.stop)
    ]
    return filtered_data

def plot_trajectory(figure, driver, lap, data) -> plotly.graph_objects.Figure:
    figure.add_trace(
        plotly.graph_objects.Scatter(
            x=data["Car Coord X"],
            y=data["Car Coord Y"],
            name=f"{driver}, Tour n°{lap}",
        )
    )
    return figure


def plot_background(figure, selected_section: Section):
    if selected_section.image is None:
        return figure
    width = abs(dx(selected_section.top_left, selected_section.bottom_right, method='cartesian'))
    height = abs(dy(selected_section.top_left, selected_section.bottom_right, method='cartesian'))
    figure.add_layout_image(
        x=selected_section.top_left.x,
        y=selected_section.bottom_right.y,
        sizex=width,
        sizey=height,
        xref="x",
        yref="y",
        opacity=1.0,
        layer="below",
        source=selected_section.image,
        sizing='stretch',
        xanchor="left",
        yanchor="bottom",
    )
    return figure


def plot_gg_diagram(figure, driver, lap, data):
    figure.add_trace(
        plotly.graph_objects.Scatter(
            x=data["CG Accel Lateral"],
            y=data["CG Accel Longitudinal"],
            name=f"{driver}, Tour n°{lap}",
        )
    )
    return figure


def default_plot_vs_car_pos_norm(figure, driver, lap, data, y_field):
    figure.add_trace(
        plotly.graph_objects.Scatter(
            x= 100 * data["Car Pos Norm"],
            y=data[y_field],
            name=f"{driver}, Tour n°{lap}",
        )
    )
    return figure


