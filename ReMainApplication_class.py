
import dash
import json
import os
import pandas

from GoogleDrive_connector import synchronize

from ReRankingsPage_class import RankingsPage


class MainApplication:
    def __init__(self, data_files_path: str, app, synchronize_with_remote: bool = False):
        self.data_files_path: str = data_files_path
        self.app = app
        self.info: dict = dict()            # {driver: info_dict}
        self.data: pandas.DataFrame = pandas.DataFrame()
        self.lap_tables: pandas.DataFrame = pandas.DataFrame()
        self.selected_laps: dict = dict()   # {driver: [lap numbers]}
        self.drivers = []                   # [driver names]

        if synchronize_with_remote:
            synchronize(self.data_files_path)

        self.parse_index()
        self.import_info()
        self.import_data()
        self.set_lap_tables()

        self.home_button = dash.dcc.Button("Accueil", id="home-button", n_clicks=0)
        self.rankings_button = dash.dcc.Button('Classement', id="rankings-button", n_clicks=0)
        self.data_selection_button = dash.dcc.Button('Analyse détaillée', id="data-selection-button", n_clicks=0)
        self.displayed_page = dash.html.Div([], id="displayed-page")
        self.rankings_page = RankingsPage(self)
        self.app.layout = dash.html.Div(
            [
                dash.html.H1('Télémétrie'),
                self.home_button,
                self.rankings_button,
                self.data_selection_button,
                self.displayed_page,
                # self.rankings_page.page,
            ],
            className='dbc dbc-ag-grid',
        )
        self.setup_callbacks()

    def setup_callbacks(self):
        self.app.callback(
            [
                dash.dependencies.Output("displayed-page", "children"),
                dash.dependencies.Input("home-button", "n_clicks"),
                dash.dependencies.Input("rankings-button", "n_clicks"),
             ])(self.show_page)

    def show_page(self, _, __):
        match dash.ctx.triggered_id:
            case "home-button":
                return [dash.html.Div([])]
            case "rankings-button":
                return [self.rankings_page.page]
            case _:
                return [dash.html.H1("Page not found")]

    def parse_index(self):
        index_file_path = os.path.join(self.data_files_path, "index.txt")
        with open(index_file_path, 'r') as file:
            lines = file.read().splitlines()

        drivers = []
        for line in lines:
            if not line: continue
            file_name, identifier = line.split("|")
            file_name = file_name.strip()
            if file_name == "index.txt": continue
            driver_name, content_type = file_name.split("-")
            driver_name = driver_name.strip()
            if driver_name not in drivers:
                drivers.append(driver_name)
        self.drivers = drivers

    def import_info(self):
        for driver in self.drivers:
            info_file_path = os.path.join(self.data_files_path, driver + " - Info.json")
            with open(info_file_path, 'r') as file:
                info_dict = json.load(file)
            self.info[driver] = info_dict

    def import_data(self):
        data = pandas.DataFrame()
        for driver in self.drivers:
            data_file_path = os.path.join(self.data_files_path, driver + " - Data.csv.gz")
            df = pandas.read_csv(
                data_file_path,
                index_col=0,
            )
            df["Driver"] = driver
            data = pandas.concat([data, df])
        self.data = data.copy()

    def set_lap_tables(self):
        self.lap_tables = pandas.DataFrame()
        for driver, info in self.info.items():
            lap_number_series = [int(lap_number_str) for lap_number_str in info["Lap times"].keys()]
            df = pandas.DataFrame({
                "Driver": driver,
                "Lap number": lap_number_series,
                "LapTimeFloat": info["Lap times"].values(),
                "Lap time": [seconds_to_time_str(time_float) for time_float in info["Lap times"].values()],
                "IsValid": info["Laps valid"].values(),
            })
            for sector_name in info["Sector times"].keys():
                sector_times = info["Sector times"][sector_name].values()
                df[sector_name.replace(" ", "") + "Float"] = sector_times
                df[sector_name] = [seconds_to_time_str(time_float) for time_float in sector_times]
            self.lap_tables = pandas.concat([self.lap_tables, df])



def seconds_to_time_str(time_in_seconds: float) -> str:
    minutes, seconds = divmod(time_in_seconds, 60)
    seconds, milliseconds = divmod(seconds, 1)
    if not minutes:
        return f"{int(seconds):02d}.{int(milliseconds*1_000):03d}"
    return f"{int(minutes):02d}:{int(seconds):02d}.{int(milliseconds*1_000):03d}"


def main():
    app = dash.Dash(
        __name__,
        # external_stylesheets=[dbc.themes.SUPERHERO, dbc_css],
        suppress_callback_exceptions=True,
    )
    # app = None
    object_instance = MainApplication(data_files_path='compressed_data', app=app, synchronize_with_remote=False)
    server = app.server
    app.run(debug=True)


if __name__ == "__main__":
    main()