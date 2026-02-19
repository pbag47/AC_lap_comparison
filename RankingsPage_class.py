
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
        self.lap_time_tables_list = []
        self.set_layout()
        self.plot_lap_times_graph()
        self.plot_lap_times_tables()
        self.page = dash.html.Div([
            # dash.html.H3('Analyse tour-par-tour'),
            dash.dcc.Graph(
                figure=self.lap_times_figure,
                id='graph-lap-times-figure',
            ),
            *[dash.dcc.Graph(
                figure=table_figure,
                id="table_lap_"+driver,
            ) for driver, table_figure in self.lap_time_tables.items()],
            *self.lap_time_tables_list,
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
            )
        )

    def plot_lap_times_graph(self):
        for driver, laps in self._app.laps.items():
            symbols= ["circle" if lap.is_valid and lap.is_complete else "arrow-up" for lap in laps]  # "x"
            data_frame = pandas.DataFrame({
                "number": [lap.number for lap in laps],
                "time": [lap.lap_time for lap in laps]
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

    def get_best_times(self):
        best_lap = 999_999
        best_s1 = 999_999
        best_s2 = 999_999
        best_s3 = 999_999
        for driver, laps in self._app.laps.items():
            for lap in laps:
                best_lap, best_s1, best_s2, best_s3 = check_if_time_is_best(lap, best_lap, best_s1, best_s2, best_s3)
        return best_lap, best_s1, best_s2, best_s3

    def get_personal_best_times(self, driver):
        best_lap = 999_999
        best_s1 = 999_999
        best_s2 = 999_999
        best_s3 = 999_999
        for lap in self._app.laps[driver]:
            best_lap, best_s1, best_s2, best_s3 = check_if_time_is_best(lap, best_lap, best_s1, best_s2, best_s3)
        return best_lap, best_s1, best_s2, best_s3

    def plot_lap_times_tables(self):
        best_lap, best_s1, best_s2, best_s3 = self.get_best_times()
        for driver, laps in self._app.laps.items():
            personal_best_lap, personal_best_s1, personal_best_s2, personal_best_s3 = self.get_personal_best_times(driver)
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
                                [round(lap.sectors[0].sector_time, 3) for lap in laps],
                                [round(lap.sectors[1].sector_time, 3) for lap in laps],
                                [round(lap.sectors[2].sector_time, 3) for lap in laps],
                            ],
                            align='right',
                            fill_color=[
                                ["red" if not lap.is_complete else "purple" if lap.lap_time == best_lap else "green" if lap.lap_time == personal_best_lap else "black" for lap in laps],
                                ["red" if not lap.is_complete else "purple" if lap.lap_time == best_lap else "green" if lap.lap_time == personal_best_lap else "black" for lap in laps],
                                ["red" if not lap.is_complete else "purple" if lap.sectors[0].sector_time == best_s1 else "green" if lap.sectors[0].sector_time == personal_best_s1 else "black" for lap in laps],
                                ["red" if not lap.is_complete else "purple" if lap.sectors[1].sector_time == best_s2 else "green" if lap.sectors[1].sector_time == personal_best_s2 else "black" for lap in laps],
                                ["red" if not lap.is_complete else "purple" if lap.sectors[2].sector_time == best_s3 else "green" if lap.sectors[2].sector_time == personal_best_s3 else "black" for lap in laps],
                            ],
                        )
                    )
                ])
            fig.update_layout(title=driver)
            self.lap_time_tables[driver] = fig


def check_if_time_is_best(lap, best_lap, best_s1, best_s2, best_s3):
    if not lap.is_complete: # \  TODO: detect invalid laps
            # or not lap.is_valid:
        return best_lap, best_s1, best_s2, best_s3
    if lap.lap_time < best_lap:
        best_lap = lap.lap_time
    if lap.sectors[0].sector_time < best_s1:
        best_s1 = lap.sectors[0].sector_time
    if lap.sectors[1].sector_time < best_s2:
        best_s2 = lap.sectors[1].sector_time
    if lap.sectors[2].sector_time < best_s3:
        best_s3 = lap.sectors[2].sector_time
    return best_lap, best_s1, best_s2, best_s3
