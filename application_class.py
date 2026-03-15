
import dash
import json
import os
import pandas

import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

from FreeDisplayPage_class import FreeDisplayPage
from GoogleDrive_connector import synchronize
from Lap_class import Lap
from LapAnalysisPage_class import LapAnalysisPage
from LapSelectorPage_class import LapSelectorPage
from RankingsPage_class import RankingsPage


load_figure_template('SUPERHERO')


class MainApplication:
    def __init__(self, data_files_path: str, app):
        self.data_files_path: str = data_files_path
        self.app = app
        self.laps: dict[str: list[Lap]] = dict() # {driver: list[Laps]}
        self.info: dict[str: dict] = dict() # {driver: {info_name: info_value}}
        self.data: dict[str: dict] = dict() # {driver: {data_name: data_values}}
        self.fields: list[str] = []  # [name]
        self.selected_laps: dict[str: list[Lap]] = dict() # {driver: list[Laps]}
        self.best_lap: Lap | None = None
        self.best_s1: Lap | None = None
        self.best_s2: Lap | None = None
        self.best_s3: Lap | None = None
        self.personal_best_lap: dict[str: Lap] = dict()
        self.personal_best_s1: dict[str: Lap] = dict()
        self.personal_best_s2: dict[str: Lap] = dict()
        self.personal_best_s3: dict[str: Lap] = dict()
        synchronize(self.data_files_path)
        self.import_laps()
        self.import_fields()
        self.find_invalid_laps()
        self.get_best_times()
        self.get_personal_best_times()
        self.lap_analysis_page = LapAnalysisPage(self)
        self.rankings_page = RankingsPage(self)
        self.lap_selection_page = LapSelectorPage(self)
        self.free_display_page = FreeDisplayPage(self)
        self.app.layout = dash.html.Div(
            [
                dash.html.H1('Télémétrie'),
                dbc.Tabs(
                    id="analysis_tabs",
                    active_tab='tab-rankings',
                    children=[
                        dbc.Tab(label='Classement', tab_id='tab-rankings'),
                        dbc.Tab(label="Sélection des données", tab_id="tab-selection"),
                        dbc.Tab(label='Analyse tour par tour', tab_id='tab-lap'),
                        dbc.Tab(label='Affichage libre', tab_id='tab-free')
                    ],
                ),
                dash.html.Div(id='analysis_page'),
            ],
            className='dbc dbc-ag-grid',
        )
        self.set_callbacks()

    def import_laps(self):
        json_files = [file_name for file_name in os.listdir(self.data_files_path) if file_name.endswith('.json')]
        for json_file in json_files:
            laps = json.load(open(os.path.join(self.data_files_path, json_file)), object_hook=Lap.__from_json__)
            driver = laps[0].driver
            self.laps[driver] = laps
            self.selected_laps[driver] = []
            self.data[driver] = {}

    def import_fields(self):
        with open(os.path.join("config", "fields.txt"), newline="\r\n") as file:
            self.fields = file.readlines()

    def import_info(self):
        # TODO
        pass

    def import_data(self, driver, laps_to_add, laps_to_remove):
        for lap in laps_to_remove:
            del self.data[driver][lap.number]

        for lap in laps_to_add:
            next_lap = [lap_candidate for lap_candidate in self.laps[driver] if lap_candidate.number == lap.number + 1]
            if next_lap:
                row_skip_selector = lambda x: not(lap.start_index <= x < next_lap[0].start_index)
            else:
                row_skip_selector = lambda x: not(x >= lap.start_index)
            with open(os.path.join(self.data_files_path, driver + ' - Data.csv')) as file:
                lap_data = pandas.read_csv(
                    file,
                    skiprows=row_skip_selector,
                    names=self.fields,
                )
            self.data[driver][lap.number] = lap_data

    def set_callbacks(self):
        self.app.callback(dash.dependencies.Output('analysis_page', 'children'),
            dash.dependencies.Input('analysis_tabs', 'active_tab'))(self.render_analysis)

    def get_best_times(self):
        all_laps = []
        for laps in self.laps.values():
            all_laps += laps
        best_lap, best_s1, best_s2, best_s3 = find_best_times(all_laps)
        self.best_lap = best_lap
        self.best_s1 = best_s1
        self.best_s2 = best_s2
        self.best_s3 = best_s3

    def get_personal_best_times(self):
        for driver, laps in self.laps.items():
            personal_best_lap, personal_best_s1, personal_best_s2, personal_best_s3 = find_best_times(laps)
            self.personal_best_lap[driver] = personal_best_lap
            self.personal_best_s1[driver] = personal_best_s1
            self.personal_best_s2[driver] = personal_best_s2
            self.personal_best_s3[driver] = personal_best_s3

    def find_invalid_laps(self):
        for driver, laps in self.laps.items():
            self.import_data(driver, laps, [])
            for lap in laps:
                lap_data = self.data[driver][lap.number][10:-10]
                lap_invalidated = lap_data["Lap Invalidated\r\r\n"].iloc[-1]
                lap.is_valid = lap.is_complete and not lap_invalidated and lap.number > 0
            self.import_data(driver, [], laps)

    def render_analysis(self, selected_tab):
        match selected_tab:
            case 'tab-rankings':
                sub_page = self.rankings_page.page
            case "tab-selection":
                sub_page = self.lap_selection_page.get_page()
            case 'tab-lap':
                sub_page = self.lap_analysis_page.get_page()
            case 'tab-free':
                sub_page = self.free_display_page.get_page()
            case _:
                sub_page = dash.html.Div([])
        return sub_page


def find_best_times(laps: list[Lap]):
    best_lap = None
    best_s1 = None
    best_s2 = None
    best_s3 = None
    for lap in laps:
        if not lap.is_valid:
            continue
        if best_lap is None:
            best_lap = lap
        if best_s1 is None:
            best_s1 = lap
        if best_s2 is None:
            best_s2 = lap
        if best_s3 is None:
            best_s3 = lap
        if lap.lap_time < best_lap.lap_time:
            best_lap = lap
        if lap.sectors[0].sector_time < best_s1.sectors[0].sector_time:
            best_s1 = lap
        if lap.sectors[1].sector_time < best_s2.sectors[1].sector_time:
            best_s2 = lap
        if lap.sectors[2].sector_time < best_s3.sectors[2].sector_time:
            best_s3 = lap
    return best_lap, best_s1, best_s2, best_s3


dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css"
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.SUPERHERO, dbc_css],
    suppress_callback_exceptions=True,
)
object_instance = MainApplication(data_files_path='processed_data', app=app)
server = app.server
app.run(debug=True)
