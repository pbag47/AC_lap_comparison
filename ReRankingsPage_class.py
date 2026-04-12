
import dash
import dash_ag_grid
import pandas
import plotly


class RankingsPage:
    def __init__(self, app):
        self._app = app
        self.lap_times_figure = plotly.graph_objects.Figure()
        self.lap_time_tables = []
        self.set_layout()
        self.plot_lap_times_graph()
        self.plot_lap_times_tables()
        self.page = dash.html.Div(
            [
                dash.dcc.Graph(
                    figure=self.lap_times_figure,
                    id='graph-lap-times-figure',
                ),
                *self.lap_time_tables,
            ]
        )

    def set_layout(self):
        self.lap_times_figure.update_layout(
            title="Temps au tour",
            xaxis=dict(
                title=dict(text="Tour"),
            ),
            yaxis=dict(
                tickformat="%M:%S.%f",
                title=dict(text="Temps"),
            ),
            height=250,
            margin=dict(l=10, r=10, t=30, b=30),
            # template="SUPERHERO",
        )

    def plot_lap_times_graph(self):
        for driver, info in self._app.info.items():
            self.lap_times_figure.add_trace(
                plotly.graph_objects.Scatter(
                    x=self._app.lap_tables[driver]["Lap number"],
                    y=pandas.to_datetime(self._app.lap_tables[driver]["LapTimeFloat"], unit="s"),
                    mode='markers+lines',
                    name=driver,
                    marker=dict(
                        symbol=pandas.Series(
                            "arrow-up",
                            index=self._app.lap_tables[driver].index
                        ).mask(
                            self._app.lap_tables[driver]["IsValid"] == True,
                            "circle"
                        ),
                    ),
                ),
            )

    def plot_lap_times_tables(self):
        overall_data = pandas.concat(self._app.lap_tables.values())
        overall_bests = overall_data[overall_data["IsValid"] == True].min()
        red_for_invalid = {
            "condition": "params.data.IsValid < 0.5",
            "style": {"backgroundColor": "red", "color": "white"},
        }
        for driver, info in self._app.info.items():
            personal_bests = self._app.lap_tables[driver][self._app.lap_tables[driver]["IsValid"] == True].min()
            lap_number_styling = {
                "field": "Lap number",
                "cellStyle": {
                    "styleConditions": [
                        red_for_invalid,
                        {
                            "condition": f"params.data.LapTimeFloat == {overall_bests['LapTimeFloat']}",
                            "style": {"backgroundColor": "purple", "color": "white"},
                        },
                        {
                            "condition": f"params.data.LapTimeFloat == {personal_bests['LapTimeFloat']}",
                            "style": {"backgroundColor": "green", "color": "white"},
                        },
                    ],
                }
            }
            lap_time_styling = {
                "field": "Lap time",
                "cellStyle": {
                    "styleConditions": [
                        red_for_invalid,
                        {
                            "condition": f"params.data.LapTimeFloat == {overall_bests['LapTimeFloat']}",
                            "style": {"backgroundColor": "purple", "color": "white"},
                        },
                        {
                            "condition": f"params.data.LapTimeFloat == {personal_bests['LapTimeFloat']}",
                            "style": {"backgroundColor": "green", "color": "white"},
                        },
                    ],
                }
            }
            sector_1_styling = {
                "field": "Secteur 1",
                "cellStyle": {
                    "styleConditions": [
                        red_for_invalid,
                        {
                            "condition": f"params.data.Secteur1Float == {overall_bests['Secteur1Float']}",
                            "style": {"backgroundColor": "purple", "color": "white"},
                        },
                        {
                            "condition": f"params.data.Secteur1Float == {personal_bests['Secteur1Float']}",
                            "style": {"backgroundColor": "green", "color": "white"},
                        },
                    ],
                }
            }
            sector_2_styling = {
                "field": "Secteur 2",
                "cellStyle": {
                    "styleConditions": [
                        red_for_invalid,
                        {
                            "condition": f"params.data.Secteur2Float == {overall_bests['Secteur2Float']}",
                            "style": {"backgroundColor": "purple", "color": "white"},
                        },
                        {
                            "condition": f"params.data.Secteur2Float == {personal_bests['Secteur2Float']}",
                            "style": {"backgroundColor": "green", "color": "white"},
                        },
                    ],
                }
            }
            sector_3_styling = {
                "field": "Secteur 3",
                "cellStyle": {
                    "styleConditions": [
                        red_for_invalid,
                        {
                            "condition": f"params.data.Secteur3Float == {overall_bests['Secteur3Float']}",
                            "style": {"backgroundColor": "purple", "color": "white"},
                        },
                        {
                            "condition": f"params.data.Secteur3Float == {personal_bests['Secteur3Float']}",
                            "style": {"backgroundColor": "green", "color": "white"},
                        },
                    ],
                }
            }

            grid = dash_ag_grid.AgGrid(
                id=driver+"lap-times",
                rowData=self._app.lap_tables[driver].to_dict("records"),
                columnDefs=[
                    lap_number_styling,
                    lap_time_styling,
                    sector_1_styling,
                    sector_2_styling,
                    sector_3_styling,
                ],
            )

            self.lap_time_tables.append(
                dash.html.Div(
                    [
                        dash.html.H2(driver),
                        grid
                    ]
                )
            )
