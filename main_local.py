
import dash
import dash_ag_grid
import dash_bootstrap_components
import os
import pandas
import plotly
import threading
import time

from coordinates_handler import Origin, get_sections_from_ini_file
from GoogleDrive_connector import synchronize_info, synchronize_data, update_index_file, import_files_index
from data_import import parse_index, import_info, import_data, set_lap_tables, get_rankings
from app_callbacks import get_lap_time_tables, plot_lap_times_graph, get_lap_times_comparison
from podium import build_podium
import lap_analysis
import lap_analysis_layouts


class Application:
    def __init__(self, app, data_files_path):
        self.app = app
        self.data_files_path = data_files_path
        self.index_file_name = "index.txt"

        # Download of small file
        update_index_file(os.path.join(self.data_files_path, self.index_file_name))

        self.index = import_files_index(os.path.join(self.data_files_path, self.index_file_name))
        self.sections = get_sections_from_ini_file()
        track_map_origin = Origin
        track_map_origin.setup("config/reference_points.txt")

        self.info_download_thread = threading.Thread(
            name="info_download_thread",
            target=self.sync_info,
            daemon=True,
        )
        self.data_download_thread = threading.Thread(
            name="data_download_thread",
            target=self.sync_data,
            daemon=True,
        )

        self.drivers: list[str] = parse_index(self.data_files_path, index_file_name=self.index_file_name)
        self.info: dict | None = None
        self.data: pandas.DataFrame | None = None
        self.lap_times: pandas.DataFrame | None = None
        self.rankings: pandas.DataFrame | None = None

        figure = plot_lap_times_graph(self.drivers, self.lap_times)
        self.app.layout = dash.html.Div(
            [
                dash.html.H1('Challenge CREA - Résultats', style={"margin": "30px"}),
                dash.html.Div([build_podium(self.rankings)], id="podium"),
                dash.html.Div(
                    [
                        dash.html.H2("Détail des tours", style={"margin": "30px"}),
                        dash.dcc.Loading(
                            [dash.dcc.Graph(figure=figure, id="lap-times-graph")],
                            id="rankings-loading",
                            display="show",
                        ),
                        dash.html.Div([], id="lap-times-tables"),
                    ],
                    id="rankings-page",
                ),
                dash.html.Div([], id="lap-times-comparison-page"),
                dash.dcc.Loading(
                    [dash.html.Div([], id="lap-analysis-page")],
                    id="lap-analysis-loading",
                    display="show",
                ),
                dash.dcc.Interval(id="refresh-info-timer", interval=1_000, n_intervals=0),
                # dash.dcc.Interval(id="refresh-data-timer", interval=5_000, n_intervals=0),
            ],
        )
        self.setup_callbacks()
        self.info_download_thread.start()
        # self.data_download_thread.start()

    def sync_info(self):
        """
        This function is executed in a separate thread
        """
        synchronize_info(self.data_files_path, self.index)
        time.sleep(10)
        self.info = import_info(self.data_files_path, self.drivers)
        self.lap_times = set_lap_tables(self.info)
        self.rankings = get_rankings(self.drivers, self.lap_times)

    def sync_data(self):
        """
        This function is executed in a separate thread
        """
        synchronize_data(self.data_files_path, self.index)
        self.data = import_data(self.data_files_path, self.drivers)

    def info_download_check(self, _) -> (bool, str, dash.html.Div, plotly.graph_objects.Figure, list):
        disable_timer = False
        loading_display = "show"
        if self.info and not self.info_download_thread.is_alive():
            disable_timer = True
            loading_display = "hide"
        podium = build_podium(self.rankings)
        figure = plot_lap_times_graph(self.drivers, self.lap_times)
        tables = get_lap_time_tables(self.drivers, self.lap_times)
        return disable_timer, loading_display, podium, figure, tables

    def data_download_check(self, _):
        disable_timer = False
        if self.data and not self.data_download_thread.is_alive():
            disable_timer = True
        return disable_timer

    def setup_callbacks(self):
        self.app.callback(
            [
                dash.dependencies.Output("refresh-info-timer", "disabled"),
                dash.dependencies.Output("rankings-loading", "display"),
                dash.dependencies.Output("podium", "children"),
                dash.dependencies.Output("lap-times-graph", "figure"),
                dash.dependencies.Output("lap-times-tables", "children"),
                dash.dependencies.Input("refresh-info-timer", "n_intervals"),
            ])(self.info_download_check)
        # self.app.callback(
        #     [
        #         dash.dependencies.Output("refresh-data-timer", "disabled"),
        #         dash.dependencies.Input("refresh-data-timer", "n_intervals"),
        #     ])(self.data_download_check)
        self.app.callback(
            [
                dash.dependencies.Output("lap-times-comparison-page", "children"),
                *[dash.dependencies.Input(driver + "lap-times", "selectedRows") for driver in self.drivers],
            ])(self.lap_times_comparison_page_callback)
        self.app.callback(
            [
                dash.dependencies.Output("lap-analysis-page", "children"),
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


def main(data_files_path: str) -> dash.Dash:
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dash_bootstrap_components.themes.SUPERHERO,
            dash_ag_grid.themes.ALPINE,
        ],
        suppress_callback_exceptions=True,
        serve_locally=True,
    )
    Application(app, data_files_path)
    return app


if __name__ == "__main__":
    application = main(
        # data_files_path="compressed_data",
        data_files_path="test",
    )
    application.run(debug=True)
