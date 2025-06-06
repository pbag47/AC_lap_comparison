import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects

from data_container import general_time_plot


def get_session_page(data, time_scales) -> dash.html.Div:
    figure = plotly.graph_objects.Figure()
    general_time_plot(figure, data, time_scales, 'tire_temp_inner_fl')
    general_time_plot(figure, data, time_scales, 'tire_temp_middle_fl')
    general_time_plot(figure, data, time_scales, 'tire_temp_outer_fl')
    output = dash.html.Div([dash.html.H3('Session'),
                            dash.dcc.Graph(figure=figure)])
    return output


