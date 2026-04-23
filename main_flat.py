
import dash
import pandas

from GoogleDrive_connector import synchronize
from data_import import parse_index, import_info, import_data, set_lap_tables
from app_callbacks import get_lap_time_tables, plot_lap_times_graph, get_lap_times_comparison


class Application:
    def __init__(self, drivers, info, data, lap_times, app):
        self.drivers = drivers
        self.info = info
        self.data = data
        self.lap_times = lap_times
        self.app = app

        self.home_button = dash.html.Button("Accueil", id="home-button")
        self.rankings_button = dash.html.Button("Classement", id="rankings-button")
        self.navigation_bar = dash.html.Div([self.home_button, self.rankings_button], id="navigation-bar")
        self.rankings_page = dash.html.Div([], id="rankings-page")
        self.lap_times_comparison_page = dash.html.Div([], id="lap-times-comparison-page")
        self.lap_analysis_page = dash.html.Div([], id="lap-analysis-page")

        self.app.layout = dash.html.Div(
            [
                dash.html.H1('Télémétrie'),
                self.navigation_bar,
                self.rankings_page,
                self.lap_times_comparison_page,
                self.lap_analysis_page,
            ],
        )
        self.setup_callbacks()

    def setup_callbacks(self):
        self.app.callback(
            [
                dash.dependencies.Output(self.rankings_page, "children"),
                dash.dependencies.Input(self.home_button, "n_clicks"),
                dash.dependencies.Input(self.rankings_button, "n_clicks"),
             ])(self.rankings_page_callback)
        self.app.callback(
            [
                dash.dependencies.Output(self.lap_times_comparison_page, "children"),
                *[dash.dependencies.Input(driver + "lap-times", "selectedRows") for driver in self.drivers],
            ])(self.lap_times_comparison_page_callback)
        self.app.callback(
            [
                dash.dependencies.Output(self.lap_analysis_page, "children"),
                *[dash.dependencies.Input(driver + "lap-times", "selectedRows") for driver in self.drivers],
            ])(self.lap_analysis_page_callback)


    def rankings_page_callback(self, *_) -> list:
        match dash.ctx.triggered_id:
            case "home-button":
                return [dash.html.H1("Home")]
            case "rankings-button":
                figure = plot_lap_times_graph(self.drivers, self.lap_times)
                return [[
                    dash.dcc.Graph(figure=figure),
                    *get_lap_time_tables(self.drivers, self.lap_times)
                ]]
            case _:
                return [dash.html.H1("_")]

    def lap_times_comparison_page_callback(self, *args) -> list:
        df = pandas.DataFrame()
        for driver_data in args:
            if not driver_data: continue
            for lap_data_dict in driver_data:
                new_df = pandas.DataFrame([lap_data_dict])
                df = pandas.concat([df, new_df], ignore_index=True)
        return get_lap_times_comparison(self.info, df)

    def lap_analysis_page_callback(self, *args) -> list:
        header = dash.html.H1("Télémétrie")
        try:
            any_driver = self.data["Driver"].unique()[0]
        except IndexError:
            return [header]
        dropdown = dash.dcc.Dropdown()

        for driver_data in args:
            if not driver_data: continue
            for lap_data_dict in driver_data:
                pass
        return [[header, dropdown]]


def main(data_files_path: str, synchronize_with_remote: bool):
    if synchronize_with_remote:
        synchronize(data_files_path)

    drivers = parse_index(data_files_path)
    info = import_info(data_files_path, drivers)
    data = import_data(data_files_path, drivers)
    lap_times = set_lap_tables(info)
    # print(drivers, info, data, lap_times)
    app = dash.Dash(
        __name__,
        # external_stylesheets=[dbc.themes.SUPERHERO, dbc_css],
        suppress_callback_exceptions=True,
    )
    # app = None
    server = app.server
    Application(drivers, info, data, lap_times, app)
    app.run(debug=True)


if __name__ == "__main__":
    main(
        data_files_path="compressed_data",
        synchronize_with_remote=False,
    )
