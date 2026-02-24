
import dash
import dash_bootstrap_components as dbc
import plotly

from coordinates_handler import Origin, get_sections_from_ini_file



class LapAnalysisPage:
    def __init__(self, app):
        self._app = app
        self.track_map_figure = plotly.graph_objects.Figure()
        self.throttle_brake_figure = plotly.graph_objects.Figure()
        self.gg_graph_figure = plotly.graph_objects.Figure()
        self.sections = get_sections_from_ini_file()
        self.selected_section = "full_lap"
        options = [dict(label="Tour complet", value="full_lap")]
        for section in self.sections:
            options.append(dict(label=section.title, value=section.title))
        self.section_dropdown = dash.dcc.Dropdown(
                options=options,
                id='dropdown-sector_selection',
                # maxHeight=400,
                placeholder="Sélectionner un secteur",
            ),
        self.setup()

        self.page = dash.html.Div([
            dash.html.H3('Analyse tour-par-tour'),
            self.section_dropdown,
        ])


    def setup(self):
        self.gg_graph_figure.update_layout(
            height=175,
            width=175,
            margin=dict(l=10, r=10, t=10, b=10),
        )

        self._app.app.callback(
            [dash.dependencies.Input("dropdown-sector_selection", 'value'),
             ])(self.update_track_map)

    def update_track_map(self):
        pass

    def get_page(self):
        self.section_dropdown.value = self.selected_section
        return self.page


def void():
    figure_track_map = plotly.graph_objects.Figure()
    figure_throttle_brake = plotly.graph_objects.Figure()
    figure_gg_graph = plotly.graph_objects.Figure()
    figure_gg_graph.update_layout(
        height=175,
        width=175,
        margin=dict(l=10, r=10, t=10, b=10),
        )
    options = [dict(label="Tour complet", value="full_lap")]
    for section in sections:
        options.append(dict(label=section.title, value=section.title))
    output = dash.html.Div(
        [
            dash.html.H3('Analyse tour-par-tour'),
            dash.dcc.Dropdown(
                options=options,
                id='dropdown-sector_selection',
                maxHeight=400,
                placeholder="Sélectionner un secteur",
            ),
            dash.dcc.Slider(
                id='slider-time-scale',
                min=0,
                max=1,
                value=0,
                ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dash.dcc.Graph(
                                figure=figure_track_map,
                                id='graph-track_map',
                                ),
                        ],
                        width=6,
                        ),
                    dbc.Col(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            daq.GraduatedBar(
                                                id='bar-throttle',
                                                vertical=True,
                                                min=0,
                                                max=100,
                                                value=25,
                                                showCurrentValue=True,
                                                label='Throttle',
                                                color='green',
                                                ),
                                        ]),
                                    dbc.Col(
                                        [
                                            daq.GraduatedBar(
                                                id='bar-brake',
                                                vertical=True,
                                                min=0,
                                                max=100,
                                                value=25,
                                                showCurrentValue=True,
                                                label='Brake',
                                                color='red'
                                                ),
                                        ]),
                                    dbc.Col(
                                        [
                                            daq.GraduatedBar(
                                                id='bar-clutch',
                                                vertical=True,
                                                min=0,
                                                max=100,
                                                value=25,
                                                showCurrentValue=True,
                                                label='Clutch',
                                                color="#9B51E0",
                                                ),
                                        ]),
                                ]),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            daq.LEDDisplay(
                                                id='LED-gear',
                                                label='GEAR',
                                                value=0,
                                                ),
                                        ]),
                                    dbc.Col(
                                        [
                                            dash.dcc.Graph(
                                                figure=figure_gg_graph,
                                                id='graph-gg-display',
                                                ),
                                        ]),
                                ]),
                        ],
                        width=3,
                        ),
                ]),
            dash.dcc.Graph(
                figure=figure_throttle_brake,
                id='graph-throttle-brake-display',
                ),
        ],
        className='dbc dbc-ag-grid',
    )
    return output