
import dash
import dash_ag_grid
import dash_bootstrap_components
import pandas
import plotly

from coordinates_handler import Origin, get_sections_from_ini_file
from GoogleDrive_connector import synchronize
from data_import import parse_index, import_info, import_data, set_lap_tables
from app_callbacks import get_lap_time_tables, plot_lap_times_graph, get_lap_times_comparison
import lap_analysis
import lap_analysis_layouts


class Application:
    def __init__(self, drivers, info, data, lap_times, app):
        self.drivers = drivers
        self.sections = get_sections_from_ini_file()
        self.info = info
        self.data = data
        self.lap_times = lap_times
        self.app = app

        figure = plot_lap_times_graph(self.drivers, self.lap_times)

        self.rankings_page = dash.html.Div([
            dash.dcc.Graph(figure=figure),
            *get_lap_time_tables(self.drivers, self.lap_times)
        ], id="rankings-page")
        self.lap_times_comparison_page = dash.html.Div([], id="lap-times-comparison-page")
        self.lap_analysis_page = dash.html.Div([], id="lap-analysis-page")

        self.app.layout = dash.html.Div(
            [
                dash.html.H1('Challenge CREA - Résultats', style={"margin": "30px"}),
                self.rankings_page,
                self.lap_times_comparison_page,
                self.lap_analysis_page,
            ],
        )
        self.setup_callbacks()

    def setup_callbacks(self):
        self.app.callback(
            [
                dash.dependencies.Output(self.lap_times_comparison_page, "children"),
                *[dash.dependencies.Input(driver + "lap-times", "selectedRows") for driver in self.drivers],
            ])(self.lap_times_comparison_page_callback)
        self.app.callback(
            [
                dash.dependencies.Output(self.lap_analysis_page, "children"),
                [dash.dependencies.Input("lap-times-comparison", "selectedRows")],
                *[dash.dependencies.State(driver + "lap-times", "selectedRows") for driver in self.drivers],
            ])(self.lap_analysis_page_callback)

    def lap_times_comparison_page_callback(self, *args) -> list:
        df = pandas.DataFrame()
        for driver_data in args:
            if not driver_data: continue
            for lap_data_dict in driver_data:
                new_df = pandas.DataFrame([lap_data_dict])
                df = pandas.concat([df, new_df], ignore_index=True)
        return get_lap_times_comparison(self.info, df)

    def lap_analysis_page_callback(self, selected_rows, *args) -> list:
        selected_laps = []
        for driver_data in args:
            if not driver_data: continue
            for lap_data_dict in driver_data:
                selected_laps.append({"Driver": lap_data_dict["Driver"], "Lap": lap_data_dict["Lap number"]})
        if not selected_rows[0]:
            sector_name = "Tour complet"
        else:
            sector_name = selected_rows[0][0]["Secteur"]
        header = dash.html.H2("Télémétrie - " + sector_name, style={"margin-top": "30px", "margin-left": "30px"})
        selected_section = [section for section in self.sections if section.title == sector_name]
        if not selected_section:
            print("No section selected")
            return [header]
        track_map_figure = plotly.graph_objects.Figure()
        gg_diagram_figure = plotly.graph_objects.Figure()
        throttle_figure = plotly.graph_objects.Figure()
        brakes_figure = plotly.graph_objects.Figure()
        steering_figure = plotly.graph_objects.Figure()
        speed_figure = plotly.graph_objects.Figure()
        track_map_figure = lap_analysis.plot_background(track_map_figure, selected_section[0])
        for selected_lap in selected_laps:
            driver = selected_lap["Driver"]
            lap = selected_lap["Lap"]
            filtered_data = lap_analysis.filter_data(selected_section[0], selected_lap, self.data)
            track_map_figure = lap_analysis.plot_trajectory(track_map_figure, driver, lap, filtered_data)
            gg_diagram_figure = lap_analysis.plot_gg_diagram(gg_diagram_figure, driver, lap, filtered_data)
            throttle_figure = lap_analysis.default_plot_vs_car_pos_norm(throttle_figure, driver, lap, filtered_data, "Throttle Pos")
            brakes_figure = lap_analysis.default_plot_vs_car_pos_norm(brakes_figure, driver, lap, filtered_data,"Brake Pos")
            steering_figure = lap_analysis.default_plot_vs_car_pos_norm(steering_figure, driver, lap, filtered_data,"Steering Angle")
            speed_figure = lap_analysis.default_plot_vs_car_pos_norm(speed_figure, driver, lap, filtered_data,"Ground Speed")
        lap_analysis_layouts.apply(
            track_map_figure,
            gg_diagram_figure,
            throttle_figure,
            brakes_figure,
            steering_figure,
            speed_figure,
        )
        return [[
            header,
            dash.dcc.Graph(
                figure=track_map_figure,
                id='track-map-figure',
            ),
            dash.dcc.Graph(
                figure=gg_diagram_figure,
                id='gg-diagram-figure',
            ),
            dash.dcc.Graph(
                figure=throttle_figure,
                id='throttle-figure',
            ),
            dash.dcc.Graph(
                figure=brakes_figure,
                id='brakes-figure',
            ),
            dash.dcc.Graph(
                figure=steering_figure,
                id='steering-figure',
            ),
            dash.dcc.Graph(
                figure=speed_figure,
                id='speed-figure',
            ),
        ]]


def main(data_files_path: str, synchronize_with_remote: bool) -> dash.Dash:
    if synchronize_with_remote:
        synchronize(data_files_path)

    drivers = parse_index(data_files_path)
    info = import_info(data_files_path, drivers)
    data = import_data(data_files_path, drivers)
    lap_times = set_lap_tables(info)
    track_map_origin = Origin
    track_map_origin.setup("config/reference_points.txt")
    # print(drivers, info, data, lap_times)
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dash_bootstrap_components.themes.SUPERHERO,
            dash_ag_grid.themes.ALPINE,
        ],
        suppress_callback_exceptions=True,
    )
    Application(drivers, info, data, lap_times, app)
    return app


if __name__ == "__main__":
    application = main(
        data_files_path="compressed_data",
        synchronize_with_remote=False,
    )
    application.run(debug=True)
