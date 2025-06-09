import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly
import plotly.graph_objects
from dash_bootstrap_templates import load_figure_template

from coordinates_handler import Origin, get_sections_from_ini_file
from data_container import main, general_time_plot, general_xy_plot
# from selection import Selection


load_figure_template('SUPERHERO')

source_file = 'data/corvette_c7_laguna_seca_example.csv'
h, info_container, data = main(source_file)
Origin.setup("config/reference_points.txt")
data.set_sample_rates()
time_scales = data.get_time_scales()
sections = get_sections_from_ini_file()


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


def get_lap_analysis_page() -> dash.html.Div:
    section_names = ["s1", "s2", "s3"]
    figure_track_map = plotly.graph_objects.Figure()
    figure_throttle_brake = plotly.graph_objects.Figure()
    figure_gg_graph = plotly.graph_objects.Figure()
    figure_gg_graph.update_layout(
        height=175,
        width=175,
        margin=dict(l=10, r=10, t=10, b=10),
        )
    options = [dict(label="Tour complet", value="full_lap")]
    sections = get_sections_from_ini_file()
    for section in sections:
        options.append(dict(label=section.title, value=section.title))
    output = dash.html.Div(
        [
            dash.html.H3('Analyse tour-par-tour'),
            dash.dcc.Dropdown(
                options=options,
                id='dropdown-sector_selection',
                maxHeight=400,
                placeholder="Sélectionner un secteur",
            ),
            dash.dcc.Slider(
                id='slider-time-scale',
                min=0,
                max=1,
                value=0,
                ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dash.dcc.Graph(
                                figure=figure_track_map,
                                id='graph-track_map',
                                ),
                        ],
                        width=6,
                        ),
                    dbc.Col(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            daq.GraduatedBar(
                                                id='bar-throttle',
                                                vertical=True,
                                                min=0,
                                                max=100,
                                                value=25,
                                                showCurrentValue=True,
                                                label='Throttle',
                                                color='green',
                                                ),
                                        ]),
                                    dbc.Col(
                                        [
                                            daq.GraduatedBar(
                                                id='bar-brake',
                                                vertical=True,
                                                min=0,
                                                max=100,
                                                value=25,
                                                showCurrentValue=True,
                                                label='Brake',
                                                color='red'
                                                ),
                                        ]),
                                    dbc.Col(
                                        [
                                            daq.GraduatedBar(
                                                id='bar-clutch',
                                                vertical=True,
                                                min=0,
                                                max=100,
                                                value=25,
                                                showCurrentValue=True,
                                                label='Clutch',
                                                color="#9B51E0",
                                                ),
                                        ]),
                                ]),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            daq.LEDDisplay(
                                                id='LED-gear',
                                                label='GEAR',
                                                value=0,
                                                ),
                                        ]),
                                    dbc.Col(
                                        [
                                            dash.dcc.Graph(
                                                figure=figure_gg_graph,
                                                id='graph-gg-display',
                                                ),
                                        ]),
                                ]),
                        ],
                        width=3,
                        ),
                    
                                            
##                                    dbc.Col(
##                                        [
##                                            daq.Gauge(
##                                                id='gauge-speed',
##                                                color='orange',  # "#9B51E0",
##                                                scale=dict(
##                                                    start=0,
##                                                    interval=10,
##                                                    labelInterval=4),
##                                                showCurrentValue=True,
##                                                units='km/h',
##                                                label='Speed',
##                                                min=0,
##                                                max=220,
##                                                value=100,
##                                                digits=0,
##                                                size=104,
##                                                ),
##                                        ],
##                                        width=2,
##                                        ),
##                                ]),
##                        ],
##                        width=3,
##                        ),
##                    dbc.Col(
##                        [],
##                        width=3,
##                        )
                ]),
            dash.dcc.Graph(
                figure=figure_throttle_brake,
                id='graph-throttle-brake-display',
                ),
        ],
        className='dbc dbc-ag-grid',
    )
    return output


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
            sub_page = get_lap_analysis_page()
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
