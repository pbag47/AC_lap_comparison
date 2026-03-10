
import dash
import dash_bootstrap_components as dbc
import plotly

from coordinates_handler import Origin, get_sections_from_ini_file, Section, dx, dy


class LapAnalysisPage:
    def __init__(self, app):
        self._app = app
        self.sections_extend = 0.02
        self.track_map_origin = Origin
        self.track_map_origin.setup("config/reference_points.txt")
        self.gap_table_figure = plotly.graph_objects.Figure()
        self.track_map_figure = plotly.graph_objects.Figure()
        self.gg_figure = plotly.graph_objects.Figure()
        self.throttle_figure = plotly.graph_objects.Figure()
        self.brake_figure = plotly.graph_objects.Figure()
        self.steering_angle_figure = plotly.graph_objects.Figure()
        self.speed_figure = plotly.graph_objects.Figure()
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

        self.setup_layout()
        self.setup_callbacks()

        square_figures_component = dbc.Row([
            dbc.Col([
                dash.dcc.Graph(
                    figure=self.track_map_figure,
                    id='track-map-figure',
                )],
                width=6,
            ),
            # dbc.Col([
            #     dash.dcc.Graph(
            #         figure=self.gap_table_figure,
            #         id='gap-table-figure',
            #     )],
            #     width=2,
            # ),
            dbc.Col([
                dash.dcc.Graph(
                    figure=self.gg_figure,
                    id='gg-figure',
                )],
                width=6,
            ),
        ])

        input_components = [
            dbc.Row([
                dash.dcc.Graph(
                    figure=self.throttle_figure,
                    id='throttle-figure',
                )],
            ),
            dbc.Row([
                dash.dcc.Graph(
                    figure=self.brake_figure,
                    id='brake-figure',
                )],
            ),
            dbc.Row([
                dash.dcc.Graph(
                    figure=self.steering_angle_figure,
                    id='steering-angle-figure',
                )],
            ),
            dbc.Row([
                dash.dcc.Graph(
                    figure=self.speed_figure,
                    id='speed-figure',
                )],
            )
        ]

        self.page = dash.html.Div([
            dash.html.H3('Analyse tour-par-tour'),
            self.section_dropdown,
            dash.dcc.Graph(
                figure=self.gap_table_figure,
                id='gap-table-figure',
            ),
            square_figures_component,
            *input_components,
        ])

    def setup_layout(self):
        self.track_map_figure.update_layout(
            yaxis=dict(scaleanchor="x", scaleratio=1),
            margin=dict(l=10, r=10, t=30, b=20),
            title=dict(text="Trajectoire"),
            # width=600,
            height=450,
        )
        self.gap_table_figure.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=30, b=30),
        )
        self.gg_figure.update_layout(
            xaxis=dict(
                title=dict(text="Accélération latérale (G)"),
                range=[-2, 2],
            ),
            yaxis=dict(
                scaleanchor="x",
                scaleratio=1,
                title=dict(text="Accélération longitudinale (G)"),
                autorange="reversed",
                range=[-2, 2],
            ),
            margin=dict(l=10, r=10, t=30, b=20),
            title=dict(text="Diagramme G-G"),
            # width=600,
            height=450,
        )
        self.throttle_figure.update_layout(
            yaxis=dict(range=[0, 100]),
            height=150,
            margin=dict(l=10, r=10, t=30, b=30),
            title=dict(text="Accélérateur (%)")
        )
        self.brake_figure.update_layout(
            yaxis=dict(range=[0, 100]),
            height=150,
            margin=dict(l=10, r=10, t=30, b=30),
            title=dict(text="Frein (%)")
        )
        self.steering_angle_figure.update_layout(
            height=150,
            margin=dict(l=10, r=10, t=30, b=30),
            title=dict(text="Angle au volant (°)")
        )
        self.speed_figure.update_layout(
            height=150,
            margin=dict(l=10, r=10, t=30, b=30),
            title=dict(text="Vitesse (km/h)")
        )

    def setup_callbacks(self):
        self._app.app.callback(
            [
                dash.dependencies.Output("track-map-figure", 'figure'),
                dash.dependencies.Output("gap-table-figure", 'figure'),
                dash.dependencies.Output("gg-figure", 'figure'),
                dash.dependencies.Output("throttle-figure", 'figure'),
                dash.dependencies.Output("brake-figure", 'figure'),
                dash.dependencies.Output("steering-angle-figure", 'figure'),
                dash.dependencies.Output("speed-figure", 'figure'),
                dash.dependencies.Input("dropdown-sector_selection", 'value'),
             ])(self.update_page)

    def update_page(self, section_name: str):
        try:
            self.selected_section = [section for section in self.sections if section.title == section_name][0]
        except IndexError:
            self.selected_section = None
        self.update_track_map()
        self.update_gap_table()
        self.update_gg()
        self.update_throttle()
        self.update_brake()
        self.update_steering_angle()
        self.update_speed()
        return (
            self.track_map_figure,
            self.gap_table_figure,
            self.gg_figure,
            self.throttle_figure,
            self.brake_figure,
            self.steering_angle_figure,
            self.speed_figure,
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

    def get_section_data(self, driver, lap):
        lap_data = self._app.data[driver][lap.number][10:-10]
        if self.selected_section is None:
            return lap_data
        else:
            section_data = lap_data[lap_data["Car Pos Norm\r\r\n"] > self.selected_section.start - self.sections_extend]
            section_data = section_data[section_data["Car Pos Norm\r\r\n"] < self.selected_section.stop + self.sections_extend]
        return section_data

    def plot(self, figure: plotly.graph_objs.Figure, x_field: str, y_field: str):
        for driver, laps in self._app.selected_laps.items():
            for lap in laps:
                section_data = self.get_section_data(driver, lap)
                x_data = section_data.loc[:, x_field]
                y_data = section_data.loc[:, y_field]
                figure.add_trace(
                    plotly.graph_objects.Scatter(
                        x=x_data,
                        y=y_data,
                        name=f"{driver} - L{lap.number} - {lap}",
                    )
                )
        return figure

    def update_gap_table(self):
        # max_start_time = 0
        min_start_time = 1_000_000
        min_end_time = 1_000_000
        for driver, laps in self._app.selected_laps.items():
            for lap in laps:
                section_data = self.get_section_data(driver, lap)
                start_time = section_data.iloc[0, section_data.columns.get_loc("Lap Time (s)\r\r\n")]
                end_time = section_data.iloc[-1, section_data.columns.get_loc("Lap Time (s)\r\r\n")]
                # if start_time > max_start_time:
                #     max_start_time = start_time
                if start_time < min_start_time:
                    min_start_time = start_time
                if end_time < min_end_time:
                    min_end_time = end_time

        gaps = []
        for driver, laps in self._app.selected_laps.items():
            for lap in laps:
                section_data = self.get_section_data(driver, lap)
                # start_time_gap = max_start_time - section_data.iloc[0, section_data.columns.get_loc("Lap Time (s)\r\r\n")]
                start_time_gap = - (min_start_time - section_data.iloc[0, section_data.columns.get_loc("Lap Time (s)\r\r\n")])
                end_time_gap = - (min_end_time - section_data.iloc[-1, section_data.columns.get_loc("Lap Time (s)\r\r\n")])
                gaps.append([f"{driver} - L{lap.number} - {lap}", start_time_gap, end_time_gap])

        self.gap_table_figure = plotly.graph_objects.Figure(
            data=[
                plotly.graph_objects.Table(
                    header=dict(
                        values=[
                            '<b>Début</b>',
                            '<b>Fin</b>',
                            '<b>Delta</b>',
                        ],
                        align='center',
                    ),
                    cells=dict(
                        values=list(zip(*gaps)),
                        align='right',
                    ),
                )
            ],
            layout=dict(
                height=250,
                margin=dict(l=10, r=10, t=30, b=30),
            )
        )

    def update_track_map(self):
        self.track_map_figure.data = []
        self.track_map_figure.layout.images = []
        self.plot_background()
        self.plot(
            self.track_map_figure,
            x_field="Car Coord X (m)\r\r\n",
            y_field="Car Coord Y (m)\r\r\n",
        )

    def update_gg(self):
        self.gg_figure.data = []
        self.plot(
            self.gg_figure,
            x_field="CG Accel Lateral (G)\r\r\n",
            y_field="CG Accel Longitudinal (G)\r\r\n",
        )

    def update_throttle(self):
        self.throttle_figure.data = []
        self.plot(
            self.throttle_figure,
            x_field="Car Pos Norm\r\r\n",
            y_field="Throttle Pos (%)\r\r\n",
        )

    def update_brake(self):
        self.brake_figure.data = []
        self.plot(
            self.brake_figure,
            x_field="Car Pos Norm\r\r\n",
            y_field="Brake Pos (%)\r\r\n",
        )

    def update_steering_angle(self):
        self.steering_angle_figure.data = []
        self.plot(
            self.steering_angle_figure,
            x_field="Car Pos Norm\r\r\n",
            y_field="Steering Angle (deg)\r\r\n",
        )

    def update_speed(self):
        self.speed_figure.data = []
        self.plot(
            self.speed_figure,
            x_field="Car Pos Norm\r\r\n",
            y_field="Ground Speed (kph)\r\r\n",
        )

    def get_page(self):
        if self.selected_section is None:
            self.section_dropdown.value = "full_lap"
        else:
            self.section_dropdown.value = self.selected_section.title
        return self.page
