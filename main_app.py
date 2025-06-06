import dash
import dash_bootstrap_components as dbc
import plotly
import plotly.graph_objects
from dash_bootstrap_templates import load_figure_template

from coordinates_handler import Origin
from data_container import main, general_time_plot, general_xy_plot
# from selection import Selection


load_figure_template('SUPERHERO')

source_file = 'data/corvette_c7_laguna_seca_example.csv'
h, info_container, data = main(source_file)
Origin.setup("config/reference_points.txt")
data.set_sample_rates()
time_scales = data.get_time_scales()


def setup_main_application() -> dash.Dash:
    dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css"
    app = dash.Dash(__name__,
                    external_stylesheets=[dbc.themes.SUPERHERO, dbc_css],
                    suppress_callback_exceptions=True,
                    )
    app.layout = dash.html.Div(
        [
            dash.html.H1('Télémétrie'),
            dbc.Tabs(
                id="analysis_tabs",
                active_tab='tab-rankings',
                children=[
                    dbc.Tab(label='Classement', tab_id='tab-rankings'),
                    dbc.Tab(label='Session entière', tab_id='tab-session'),
                    dbc.Tab(label='Tour par tour', tab_id='tab-lap'),
                    dbc.Tab(label='Affichage libre', tab_id='tab-free')
                    ],
            ),
            dash.html.Div(id='analysis_page'),
            dash.html.Output(
                id='debug_output',
                children='test',
            ),
        ],
        className='dbc dbc-ag-grid',
    )
    return app


def get_free_display_page() -> dash.html.Div:
    figure_time = plotly.graph_objects.Figure()
    figure_xy = plotly.graph_objects.Figure()
    output = dash.html.Div(
        [
            dash.html.H3('Affichage libre - Séries temporelles'),
            dash.dcc.Dropdown(
                options=data.get_title_name_pairs(),
                multi=True,
                id='dropdown-y-axis-vs-time',
                maxHeight=400,
                placeholder="Sélectionner des séries",
            ),
            dash.dcc.Graph(
                figure=figure_time,
                id='graph-free-time-display',
            ),
            dash.html.H3('Affichage libre - xy'),
            dash.dcc.Dropdown(
                options=data.get_title_name_pairs(),
                id='dropdown-x-axis-xy',
                maxHeight=400,
                placeholder="Sélectionner l'axe x",
            ),
            dash.dcc.Dropdown(
                options=data.get_title_name_pairs(),
                id='dropdown-y-axis-xy',
                maxHeight=400,
                placeholder="Sélectionner l'axe y",
            ),
            dash.dcc.Graph(
                figure=figure_xy,
                id='graph-free-xy-display'
            ),
        ],
        className='dbc dbc-ag-grid',
    )
    return output


@dash.callback(dash.Output('analysis_page', 'children'),
                dash.Input('analysis_tabs', 'active_tab'))
def render_analysis(selected_tab):
    match selected_tab:
        case 'tab-rankings':
            sub_page = dash.html.Div([dash.html.H3('Rankings')])
        case 'tab-session':
            sub_page = dash.html.Div([dash.html.H3('Session')])
        case 'tab-lap':
            sub_page = dash.html.Div([dash.html.H3('Lap')])
        case 'tab-free':
            sub_page = get_free_display_page()
        case _:
            sub_page = dash.html.Div([])
    return sub_page


@dash.callback(
    dash.Output('graph-free-time-display', 'figure'),
    dash.Input('dropdown-y-axis-vs-time', 'value'),
    prevent_initial_call=True,
)
def update_free_time_graph(values):
    figure = plotly.graph_objects.Figure()
    for value in values:
        general_time_plot(figure, data, time_scales, value)
    return figure


@dash.callback(
    dash.Output('graph-free-xy-display', 'figure'),
    dash.Input('dropdown-x-axis-xy', 'value'),
    dash.Input('dropdown-y-axis-xy', 'value'),
    prevent_initial_call=True,
)
def update_free_xy_graph(x_axis, y_axis):
    figure = plotly.graph_objects.Figure()
    if x_axis is None or y_axis is None:
        return figure
    general_xy_plot(figure, data, x_axis, y_axis)
    return figure


if __name__ == '__main__':
    main_app = setup_main_application()
    main_app.run(debug=True)
