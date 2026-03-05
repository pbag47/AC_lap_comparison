
import dash
import dash_bootstrap_components as dbc
import plotly

from coordinates_handler import Origin, get_sections_from_ini_file, Section, dx, dy


class LapAnalysisPage:
    def __init__(self, app):
        self._app = app
        self.track_map_origin = Origin
        self.track_map_origin.setup("config/reference_points.txt")
        self.track_map_figure = plotly.graph_objects.Figure()
        self.throttle_figure = plotly.graph_objects.Figure()
        self.brake_figure = plotly.graph_objects.Figure()
        self.steering_angle_figure = plotly.graph_objects.Figure()
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

        self.setup_layout()
        self.setup_callbacks()

        throttle_brake_component = dbc.Col([
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
        ],
            width=True,
        )

        self.page = dash.html.Div([
            dash.html.H3('Analyse tour-par-tour'),
            self.section_dropdown,
            dbc.Row([
                dbc.Col([
                    dash.dcc.Graph(
                        figure=self.track_map_figure,
                        id='track-map-figure',
                    )],
                    width=6),
                throttle_brake_component,
            ])
        ])

    def setup_layout(self):
        self.track_map_figure.update_layout(
            yaxis=dict(scaleanchor="x", scaleratio=1),
            margin=dict(l=10, r=10, t=30, b=20),
            title=dict(text="Trajectoire")
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
            # yaxis=dict(range=[0, 100]),
            height=150,
            margin=dict(l=10, r=10, t=30, b=30),
            title=dict(text="Angle au volant (°)")
        )

        # self.gg_graph_figure.update_layout(
        #     height=175,
        #     width=175,
        #     margin=dict(l=10, r=10, t=10, b=10),
        # )

    def setup_callbacks(self):
        self._app.app.callback(
            [
                dash.dependencies.Output("track-map-figure", 'figure'),
                dash.dependencies.Output("throttle-figure", 'figure'),
                dash.dependencies.Output("brake-figure", 'figure'),
                dash.dependencies.Output("steering-angle-figure", 'figure'),
                dash.dependencies.Input("dropdown-sector_selection", 'value'),
             ])(self.update_page)

    def update_page(self, section_name: str):
        try:
            self.selected_section = [section for section in self.sections if section.title == section_name][0]
        except IndexError:
            self.selected_section = None
        self.update_track_map()
        self.update_throttle()
        self.update_brake()
        self.update_steering_angle()
        return self.track_map_figure, self.throttle_figure, self.brake_figure, self.steering_angle_figure

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

    def plot(self, figure: plotly.graph_objs.Figure, x_field: str, y_field: str):
        sections_extend = 0.02
        if self.selected_section is None:
            for driver, laps in self._app.selected_laps.items():
                for lap in laps:
                    lap_data = self._app.data[driver][lap.number][10:-10]
                    x_data = lap_data.loc[:, x_field]
                    y_data = lap_data.loc[:, y_field]
                    figure.add_trace(
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
                    section_data = lap_data[lap_data["Car Pos Norm\r\r\n"] > self.selected_section.start - sections_extend]
                    section_data = section_data[section_data["Car Pos Norm\r\r\n"] < self.selected_section.stop + sections_extend]
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

    def update_track_map(self):
        self.track_map_figure.data = []
        self.track_map_figure.layout.images = []
        self.plot_background()
        self.plot(
            self.track_map_figure,
            x_field="Car Coord X (m)\r\r\n",
            y_field="Car Coord Y (m)\r\r\n",
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

    def get_page(self):
        if self.selected_section is None:
            self.section_dropdown.value = "full_lap"
        else:
            self.section_dropdown.value = self.selected_section.title
        return self.page
