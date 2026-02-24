
import dash
import dash_bootstrap_components as dbc


class LapSelectorPage:
    def __init__(self, app):
        self._app = app
        self.dropdowns = []
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
            component = dbc.Row([
                dbc.Col([dash.html.H6(driver, style={"text-align": "right"})], width=3),
                dbc.Col([dropdown], width=True),
            ], align="center")
            self.dropdowns.append(dropdown)
            self.selector_components.append(component)

    def get_page(self):
        for dropdown in self.dropdowns:
            driver, _ = dropdown.id.split("|")
            dropdown.value = [lap.number for lap in self._app.selected_laps[driver]]
        return self.page

    def update_selected_laps(self, values: list[int], dropdown_identifier: str):
        driver, _ = dropdown_identifier.split("|")
        self._app.selected_laps[driver] = [lap for lap in self._app.laps[driver] if lap.number in values]
        self._app.import_data()

