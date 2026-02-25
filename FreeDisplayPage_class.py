from unittest import case

import dash
import dash_bootstrap_components as dbc
import plotly


class FreeDisplayPage:
    def __init__(self, app):
        self._app = app

        self.time_graph_figure = plotly.graph_objects.Figure()
        self.xy_graph_figure = plotly.graph_objects.Figure()

        self.time_graph_y_dropdown_value = None
        self.time_graph_y_dropdown = dash.dcc.Dropdown(
            self._app.fields,
            multi=True,
            id='y_time',
            # maxHeight=400,
            placeholder="Sélectionner des séries",
        )
        self.xy_graph_x_dropdown = dash.dcc.Dropdown(
            self._app.fields,
            id='x_xy',
            # maxHeight=400,
            placeholder="Sélectionner l'axe x",
        )
        self.xy_graph_y_dropdown = dash.dcc.Dropdown(
            self._app.fields,
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
             ])(self.update_time_graph)

    def update_xy_graph(self, values: str | list[str], identifier: str):
        match identifier:
            case "x_xy":
                pass
            case "y_xy":
                pass

    def update_time_graph(self, value: str) -> plotly.graph_objects.Figure:
        figure = plotly.graph_objects.Figure()
        for driver, laps in self._app.selected_laps.items():
            for lap in laps:
                # x_data = self._app.data[driver][lap.number].loc[:, "time (s)"]
                y_data = self._app.data[driver][lap.number].loc[:, value]
                figure.add_trace(
                    plotly.graph_objects.Scatter(
                        x=[i for i in range(len(y_data))],  # x_data,
                        y=y_data,
                    )
                )
        # self.time_graph_figure = figure
        return figure

    def get_page(self):
        # print("get_page")
        # self.update_dropdowns()
        # print(self.page)
        return self.page
