
import dash
import pandas
import plotly

from time import strftime
from time import gmtime


class RankingsPage:
    def __init__(self, app):
        self._app = app
        self.lap_times_figure = plotly.graph_objects.Figure()
        self.lap_time_tables = {}
        self.set_layout()
        self.plot_lap_times_graph()
        self.plot_lap_times_tables()
        self.page = dash.html.Div([
            dash.dcc.Graph(
                figure=self.lap_times_figure,
                id='graph-lap-times-figure',
            ),
            *[dash.dcc.Graph(
                figure=table_figure,
                id="table_lap_"+driver,
            ) for driver, table_figure in self.lap_time_tables.items()],
        ])

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
        )

    def plot_lap_times_graph(self):
        for driver, laps in self._app.laps.items():
            symbols= ["circle" if lap.is_valid and lap.is_complete else "arrow-up" for lap in laps]  # "x"
            data_frame = pandas.DataFrame({
                "number": [lap.number for lap in laps if lap.is_valid],
                "time": [lap.lap_time for lap in laps if lap.is_valid],
            })
            self.lap_times_figure.add_trace(
                plotly.graph_objects.Scatter(
                    x=data_frame["number"],
                    y=pandas.to_datetime(data_frame['time'], unit="s"),
                    mode='markers+lines',
                    name=driver,
                    marker=dict(symbol=symbols),
                ),
            )

    def plot_lap_times_tables(self):
        for driver, laps in self._app.laps.items():
            fig = plotly.graph_objects.Figure(
                data=[
                    plotly.graph_objects.Table(
                        header=dict(
                            values=[
                                '<b>Tour</b>',
                                '<b>Temps</b>',
                                '<b>Secteur 1</b>',
                                '<b>Secteur 2</b>',
                                '<b>Secteur 3</b>',
                            ],
                            align='center',
                        ),
                        cells=dict(
                            values=[
                                [lap.number for lap in laps],
                                [strftime("%M:%S", gmtime(round(lap.lap_time, 3))) + "." + str(round(lap.lap_time % 1 * 1_000)) for lap in laps],
                                [f"{lap.sectors[0].sector_time: .3f}" for lap in laps],
                                [f"{lap.sectors[1].sector_time: .3f}" for lap in laps],
                                [f"{lap.sectors[2].sector_time: .3f}" for lap in laps],
                            ],
                            align='right',
                            fill_color=[
                                ["red" if not lap.is_valid else "purple" if lap == self._app.best_lap else "green" if lap == self._app.personal_best_lap[driver] else "black" for lap in laps],
                                ["red" if not lap.is_valid else "purple" if lap == self._app.best_lap else "green" if lap == self._app.personal_best_lap[driver] else "black" for lap in laps],
                                ["red" if not lap.is_valid else "purple" if lap == self._app.best_s1 else "green" if lap == self._app.personal_best_s1[driver] else "black" for lap in laps],
                                ["red" if not lap.is_valid else "purple" if lap == self._app.best_s2 else "green" if lap == self._app.personal_best_s2[driver] else "black" for lap in laps],
                                ["red" if not lap.is_valid else "purple" if lap == self._app.best_s3 else "green" if lap == self._app.personal_best_s3[driver] else "black" for lap in laps],
                            ],
                        )
                    )
                ])
            fig.update_layout(
                title=driver,
                margin=dict(l=10, r=10, t=30, b=30),
                height=350,
            )
            self.lap_time_tables[driver] = fig
