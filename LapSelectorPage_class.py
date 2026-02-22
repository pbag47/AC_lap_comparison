
import dash


class LapSelectorPage:
    def __init__(self, app):
        self._app = app
        self.dropdown_ids = []
        self.selector_components = []
        self.setup()

        self.page = dash.html.Div([
            dash.html.H3('Sélection des tours à analyser'),
            *self.selector_components,
        ])

    def setup(self):
        self.selector_components = []
        for driver, laps in self._app.laps.items():
            dropdown_id = "|".join([driver, "lap_selector"])
            dropdown = dash.dcc.Dropdown(
                [{
                    "label": dash.html.Span(
                        [str(lap)],
                        style={
                            'color': "red" if not lap.is_complete else "green" if lap == self._app.personal_best_lap[driver] else "white",
                        }
                    ),
                    "value": lap.number,
                } for lap in laps],
                id=dropdown_id,
                multi=True,
            )
            self._app.app.callback(
                [dash.dependencies.Input(dropdown_id, 'value'),
                 dash.dependencies.Input(dropdown_id, 'id'),
                 ])(self.update_selected_laps)
            self.selector_components.append(dropdown)

    def update_selected_laps(self, values: list[int], dropdown_identifier: str):
        driver, _ = dropdown_identifier.split("|")
        self._app.selected_laps[driver] = values


