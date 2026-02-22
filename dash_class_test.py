
import dash
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import dash_daq as daq
import json
import os
import plotly
import plotly.graph_objects

from coordinates_handler import Origin, get_sections_from_ini_file
from data_container import main, general_time_plot, general_xy_plot, plot_trajectory, InfoContainer
from Lap_class import Lap
from LapAnalysisPage_class import LapAnalysisPage
from LapSelectorPage_class import LapSelectorPage
from RankingsPage_class import RankingsPage


load_figure_template('SUPERHERO')


class MainApplication:
    def __init__(self):
        self.laps: dict[str: list[Lap]] = dict() # {driver: list[Laps]}
        self.info: dict[str: dict] = dict() # {driver: {info_name: info_value}}
        self.data: dict[str: dict] = dict() # {driver: {data_name: data_values}}
        self.selected_laps: dict[str: list[Lap]] = dict() # {driver: list[Laps]}
        self.best_lap: Lap | None = None
        self.best_s1: Lap | None = None
        self.best_s2: Lap | None = None
        self.best_s3: Lap | None = None
        self.personal_best_lap: dict[str: Lap] = dict()
        self.personal_best_s1: dict[str: Lap] = dict()
        self.personal_best_s2: dict[str: Lap] = dict()
        self.personal_best_s3: dict[str: Lap] = dict()
        self.import_laps()
        dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css"
        self.app = dash.Dash(__name__,
                        external_stylesheets=[dbc.themes.SUPERHERO, dbc_css],
                        suppress_callback_exceptions=True,
                        )
        self.lap_analysis_page = LapAnalysisPage(self)
        self.rankings_page = RankingsPage(self)
        self.lap_selection_page = LapSelectorPage(self)
        self.app.layout = dash.html.Div(
            [
                dash.html.H1('Télémétrie'),
                dbc.Tabs(
                    id="analysis_tabs",
                    active_tab='tab-rankings',
                    children=[
                        dbc.Tab(label='Classement', tab_id='tab-rankings'),
                        dbc.Tab(label="Sélection", tab_id="tab-selection"),
                        dbc.Tab(label='Session entière', tab_id='tab-session'),
                        dbc.Tab(label='Tour par tour', tab_id='tab-lap'),
                        dbc.Tab(label='Affichage libre', tab_id='tab-free')
                    ],
                ),
                dash.html.Div(id='analysis_page'),
                dash.html.Output(
                    id='debug_output',
                    children='test',
                ),
            ],
            className='dbc dbc-ag-grid',
        )
        self.set_callbacks()

    def import_laps(self):
        files_location = "processed_data"
        json_files = [file_name for file_name in os.listdir(files_location) if file_name.endswith('.json')]
        for json_file in json_files:
            laps = json.load(open(os.path.join(files_location, json_file)), object_hook=Lap.__from_json__)
            driver = laps[0].driver
            self.laps[driver] = laps
            self.selected_laps[driver] = []
        self.get_best_times()
        self.get_personal_best_times()

    def import_info(self):
        # TODO
        pass

    def import_data(self):
        # TODO
        pass

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

    def render_analysis(self, selected_tab):
        match selected_tab:
            case 'tab-rankings':
                sub_page = self.rankings_page.page
            case "tab-selection":
                sub_page = self.lap_selection_page.get_page()
            case 'tab-session':
                sub_page = dash.html.Div([dash.html.H3('Session')])
            case 'tab-lap':
                sub_page = dash.html.Div([dash.html.H3('Lap')])
                # sub_page = self.lap_analysis_page.page
            case 'tab-free':
                sub_page = dash.html.Div([dash.html.H3('Session')]) # get_free_display_page()
            case _:
                sub_page = dash.html.Div([])
        return sub_page


def find_best_times(laps: list[Lap]):
    best_lap = None
    best_s1 = None
    best_s2 = None
    best_s3 = None
    for lap in laps:
        if not lap.is_complete:  # \  TODO: detect invalid laps
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


if __name__ == '__main__':
    main_app = MainApplication()
    main_app.app.run(debug=True)
