import dash
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

from MainApplication_class import MainApplication


def main():
    load_figure_template('SUPERHERO')
    dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css"
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.SUPERHERO, dbc_css],
        suppress_callback_exceptions=True,
    )
    object_instance = MainApplication(data_files_path='test', app=app, synchronize_with_remote=False)
    server = app.server
    app.run(debug=True)

if __name__ == '__main__':
    main()