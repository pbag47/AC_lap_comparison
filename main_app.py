# from dash import Dash, dcc, html, Input, Output, callback
import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

from coordinates_handler import Origin, plot_track_map
from data_container import DataContainer
from selection import Selection


load_figure_template('SUPERHERO')


def setup_main_application() -> dash.Dash:
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO])
    app.layout = dash.html.Div([
                dash.html.H1('Télémétrie'),
                dbc.Tabs(id="analysis_tabs", active_tab='rankings', children=[
                    dbc.Tab(label='Classement', tab_id='rankings'),
                    dbc.Tab(label='Session entière', tab_id='session'),
                    dbc.Tab(label='Tour par tour', tab_id='lap'),
                    ]),
                dash.html.Div(id='analysis_page'),
                dash.html.Output(id='debug_output', children='test'),
                ])
    return app


@dash.callback([dash.Output('analysis_page', 'children'),
                        dash.Output('debug_output', 'children')],
                dash.Input('analysis_tabs', 'active_tab'))
def render_analysis(selected_tab):
    output = selected_tab
    match selected_tab:
        case 'rankings':
            sub_page = dash.html.Div([dash.html.H3('rankings')])
        case 'session':
            sub_page = dash.html.Div([dash.html.H3('session')])
        case 'lap':
            sub_page = dash.html.Div([dash.html.H3('lap')])
        case _:
            sub_page = dash.html.Div([])
    return sub_page, output



if __name__ == '__main__':
    main_app = setup_main_application()
    main_app.run(debug=True)
