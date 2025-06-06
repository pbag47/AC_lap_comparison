# from dash import Dash, dcc, html, Input, Output, callback
import dash
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

from coordinates_handler import Origin, plot_track_map
from data_container import DataContainer, main, general_time_plot, general_xy_plot
from selection import Selection
from pages.session_page import get_session_page


load_figure_template('SUPERHERO')

source_file = 'data/corvette_c7_laguna_seca_example.csv'
h, info_container, data_container = main(source_file)
Origin.setup("config/reference_points.txt")
data_container.set_sample_rates()
data_time_scales = data_container.get_time_scales()


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
            sub_page = dash.html.Div([dash.html.H3('Rankings')])
        case 'session':
            sub_page = get_session_page(data_container, data_time_scales)
        case 'lap':
            sub_page = dash.html.Div([dash.html.H3('Lap')])
        case _:
            sub_page = dash.html.Div([])
    return sub_page, output



if __name__ == '__main__':
    main_app = setup_main_application()
    main_app.run(debug=True)
