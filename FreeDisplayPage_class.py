
import dash
import plotly


class FreeDisplayPage:
    def __init__(self, app):
        self._app = app

        self.selected_time_values: list[str] = []
        self.selected_xy_values: tuple[str, list[str]] = ("", [])

        self.time_graph_figure = plotly.graph_objects.Figure()
        self.xy_graph_figure = plotly.graph_objects.Figure()

        self.time_graph_figure.update_layout(legend=dict(groupclick="toggleitem"))
        self.xy_graph_figure.update_layout(legend=dict(groupclick="toggleitem"))

        self.time_graph_y_dropdown_value = None
        self.time_graph_y_dropdown = dash.dcc.Dropdown(
            self._app.fields,
            multi=True,
            id='y_time',
            maxHeight=400,
            placeholder="Sélectionner des séries",
        )
        self.xy_graph_x_dropdown = dash.dcc.Dropdown(
            self._app.fields,
            multi=False,
            id='x_xy',
            maxHeight=400,
            placeholder="Sélectionner l'axe x",
        )
        self.xy_graph_y_dropdown = dash.dcc.Dropdown(
            self._app.fields,
            multi=True,
            id='y_xy',
            maxHeight=400,
            placeholder="Sélectionner l'axe y",
        )

        self.page = dash.html.Div([
            dash.html.H3('Affichage libre - Séries temporelles'),
            self.time_graph_y_dropdown,
            dash.dcc.Graph(
                figure=self.time_graph_figure,
                id='graph-time-figure',
            ),
            dash.html.H3('Affichage libre - X & Y'),
            self.xy_graph_x_dropdown,
            self.xy_graph_y_dropdown,
            dash.dcc.Graph(
                figure=self.xy_graph_figure,
                id='graph-xy-figure',
            ),
        ])
        self.setup_callbacks()

    def setup_callbacks(self):
        self._app.app.callback(
            [
                dash.dependencies.Output("graph-time-figure", 'figure'),
                dash.dependencies.Input("y_time", 'value'),
             ],
            prevent_initial_call=True,
        )(self.update_time_graph)
        self._app.app.callback(
            [
                dash.dependencies.Output("graph-xy-figure", 'figure'),
                dash.dependencies.Input("x_xy", 'value'),
                dash.dependencies.Input("y_xy", 'value'),
             ],
            prevent_initial_call=True,
        )(self.update_xy_graph)

    def update_xy_graph(self, x_field: str, y_fields: list[str]):
        self.xy_graph_figure.data = []
        self.selected_xy_values = x_field, y_fields
        if not x_field or not y_fields:
            return [self.xy_graph_figure]
        for y_field in y_fields:
            for driver, laps in self._app.selected_laps.items():
                for lap in laps:
                    x_data = self._app.data[driver][lap.number].loc[:, x_field]
                    y_data = self._app.data[driver][lap.number].loc[:, y_field]
                    self.xy_graph_figure.add_trace(
                        plotly.graph_objects.Scatter(
                            x=x_data,
                            y=y_data,
                            name=f"{driver} - L{lap.number} - {lap}",
                            legendgroup=y_field,
                            legendgrouptitle_text=y_field,
                        )
                    )
        self.xy_graph_figure.update_layout(
            xaxis=dict(
                title=dict(
                    text=x_field,
                )
            )
        )
        return [self.xy_graph_figure]

    def update_time_graph(self, values: list[str]) -> plotly.graph_objects.Figure:
        self.time_graph_figure.data = []
        self.selected_time_values = values
        if not values:
            return [self.time_graph_figure]
        for value in values:
            for driver, laps in self._app.selected_laps.items():
                for lap in laps:
                    x_data = self._app.data[driver][lap.number].loc[:, "time (s)\r\r\n"] - self._app.data[driver][lap.number].loc[:, "time (s)\r\r\n"][0]
                    y_data = self._app.data[driver][lap.number].loc[:, value]
                    self.time_graph_figure.add_trace(
                        plotly.graph_objects.Scatter(
                            x=x_data,
                            y=y_data,
                            name=f"{driver} - L{lap.number} - {lap}",
                            legendgroup=value,
                            legendgrouptitle_text=value,
                        )
                    )
        return [self.time_graph_figure]

    def get_page(self):
        self.time_graph_y_dropdown.value = self.selected_time_values
        self.xy_graph_x_dropdown.value = self.selected_xy_values[0]
        self.xy_graph_y_dropdown.value = self.selected_xy_values[1]
        self.update_time_graph(values=self.selected_time_values)
        self.update_xy_graph(x_field=self.selected_xy_values[0], y_fields=self.selected_xy_values[1])
        return self.page
