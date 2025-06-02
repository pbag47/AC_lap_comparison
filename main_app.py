from unittest import case

# from dash import Dash, dcc, html, Input, Output, callback
import dash
import dash_mantine_components as dmc

from coordinates_handler import Origin, plot_track_map
from data_container import DataContainer
from selection import Selection


class MainApp:
    def __init__(self):
        self.dash_app = dash.Dash(__name__)
        self.dash_app.layout = dash.html.Div([
                dash.html.H1('Télémétrie'),
                dash.dcc.Tabs(id="analysis_tabs", value='session', children=[
                    dash.dcc.Tab(label='Classement', value='rankings'),
                    dash.dcc.Tab(label='Session entière', value='session'),
                    dash.dcc.Tab(label='Tour par tour', value='lap'),
                ]),
                dash.html.Div(id='analysis_page')
            ])
        self.data_selection: list[Selection] = []


@dash.callback(dash.Output('analysis_page', 'children'),
                dash.Input('analysis_tabs', 'value'))
def render_analysis(selected_tab):
    match selected_tab:
        case 'rankings':
            sub_page = dash.html.Div([
                dash.html.H3('rankings'),
            ])
        case 'session':
            sub_page = dash.html.Div([
                dash.html.H3('session'),
            ])
        case 'lap':
            sub_page = dash.html.Div([
                dash.html.H3('lap'),
            ])
        case _:
            sub_page = dash.html.Div([])
    return sub_page



if __name__ == '__main__':
    main_app = MainApp()
    main_app.dash_app.run(debug=True)
