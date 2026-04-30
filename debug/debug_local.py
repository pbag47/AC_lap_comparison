
import dash
import dash_ag_grid
import pandas
import plotly


def main() -> dash.Dash:
    app = dash.Dash(
        __name__,
        serve_locally=True,
    )
    dummy_data = pandas.DataFrame(
        {
            "Column 1": [1, 2],
            "Column 2": [3, 4],
        },
    )
    test_figure = plotly.graph_objects.Figure()
    test_figure.add_trace(
        plotly.graph_objects.Scatter(
            x=dummy_data["Column 1"],
            y=dummy_data["Column 2"],
        )
    )
    test_table = dash_ag_grid.AgGrid(
        id="test-table",
        rowData=dummy_data.to_dict("records"),
        columnDefs=[
            {"field": "Column 1"},
            {"field": "Column 2"},
        ],
    )
    app.layout = dash.html.Div(
        [
            dash.html.H1("Debug Page"),
            dash.dcc.Graph(figure=test_figure),
            test_table,
        ]
    )
    return app


if __name__ == "__main__":
    application = main()
    server = application.server
    application.run(debug=True)