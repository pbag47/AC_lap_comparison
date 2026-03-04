
import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly

from coordinates_handler import Origin, get_sections_from_ini_file, Section, dx, dy


class LapAnalysisPage:
    def __init__(self, app):
        self._app = app
        self.track_map_figure = plotly.graph_objects.Figure()
        self.track_map_origin = Origin
        self.track_map_origin.setup("config/reference_points.txt")
        self.throttle_brake_figure = plotly.graph_objects.Figure()
        self.gg_graph_figure = plotly.graph_objects.Figure()
        self.sections = get_sections_from_ini_file()
        self.selected_section: Section | None = None
        options = [dict(label="Tour complet", value="full_lap")]
        for section in self.sections:
            options.append(dict(label=section.title, value=section.title))
        self.section_dropdown = dash.dcc.Dropdown(
            options=options,
            multi=False,
            id='dropdown-sector_selection',
            maxHeight=400,
            placeholder="Sélectionner un secteur",
        )
        self.setup_callbacks()

        self.page = dash.html.Div([
            dash.html.H3('Analyse tour-par-tour'),
            self.section_dropdown,
            dash.dcc.Graph(
                figure=self.track_map_figure,
                id='track-map-figure',
            ),
        ])

    def setup_callbacks(self):
        self._app.app.callback(
            [
                dash.dependencies.Output("track-map-figure", 'figure'),
                dash.dependencies.Input("dropdown-sector_selection", 'value'),
             ])(self.update_track_map)


    def setup(self):
        self.gg_graph_figure.update_layout(
            height=175,
            width=175,
            margin=dict(l=10, r=10, t=10, b=10),
        )

    def plot_background(self):
        if self.selected_section is None:
            return
        if self.selected_section.image is None:
            return
        width = abs(dx(self.selected_section.top_left, self.selected_section.bottom_right, method='cartesian'))
        height = abs(dy(self.selected_section.top_left, self.selected_section.bottom_right, method='cartesian'))
        self.track_map_figure.add_layout_image(
            x=self.selected_section.top_left.x,
            y=self.selected_section.bottom_right.y,
            sizex=width,
            sizey=height,
            xref="x",
            yref="y",
            opacity=1.0,
            layer="below",
            source=self.selected_section.image,
            sizing='stretch',
            xanchor="left",
            yanchor="bottom",
        )
        # self.track_map_figure.update_xaxes(range=[self.selected_section.top_left.x, self.selected_section.top_left.x + width])
        # self.track_map_figure.update_yaxes(range=[self.selected_section.bottom_right.y, self.selected_section.bottom_right.y + height])

    def update_track_map(self, section_name: str):
        self.track_map_figure.data = []
        self.track_map_figure.layout.images = []
        try:
            self.selected_section = [section for section in self.sections if section.title == section_name][0]
            self.plot_background()
        except IndexError:
            self.selected_section = None

        if self.selected_section is None:
            for driver, laps in self._app.selected_laps.items():
                for lap in laps:
                    lap_data = self._app.data[driver][lap.number][10:-10]
                    x_data = lap_data.loc[:, "Car Coord X (m)\r\r\n"]
                    y_data = lap_data.loc[:, "Car Coord Y (m)\r\r\n"]
                    self.track_map_figure.add_trace(
                        plotly.graph_objects.Scatter(
                            x=x_data,
                            y=y_data,
                            name=f"{driver} - L{lap.number} - {lap}",
                        )
                    )
        else:
            for driver, laps in self._app.selected_laps.items():
                for lap in laps:
                    lap_data = self._app.data[driver][lap.number][10:-10]
                    section_data = lap_data[lap_data["Car Pos Norm\r\r\n"] > self.selected_section.start]
                    section_data = section_data[section_data["Car Pos Norm\r\r\n"] < self.selected_section.stop]
                    x_data = section_data.loc[:,"Car Coord X (m)\r\r\n"]
                    y_data = section_data.loc[:, "Car Coord Y (m)\r\r\n"]
                    self.track_map_figure.add_trace(
                        plotly.graph_objects.Scatter(
                            x=x_data,
                            y=y_data,
                            name=f"{driver} - L{lap.number} - {lap}",
                        )
                    )
        self.track_map_figure.update_yaxes(scaleanchor="x", scaleratio=1)
        return [self.track_map_figure]

    def get_page(self):
        if self.selected_section is None:
            self.section_dropdown.value = "full_lap"
        else:
            self.section_dropdown.value = self.selected_section.title
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