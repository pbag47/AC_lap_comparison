

import dash
import dash_ag_grid
import pandas
import plotly

import conditional_styling


def get_lap_time_tables(drivers: list[str], lap_times: pandas.DataFrame) -> list:
    output = []
    overall_bests = lap_times[lap_times["IsValid"] == True].min()
    red_for_invalid = {
        "condition": "params.data.IsValid < 0.5",
        "style": {"backgroundColor": "red", "color": "white"},
    }
    for driver in drivers:
        personal_bests = lap_times[
            (lap_times["Driver"]==driver) & (lap_times["IsValid"] == True)
        ].min()
        lap_number_styling = {
            "field": "Lap number",
            "cellStyle": {
                "styleConditions": [
                    conditional_styling.get_red_for_invalid(),
                    conditional_styling.get_purple_for_best(overall_bests, "LapTimeFloat"),
                    conditional_styling.get_green_for_personal_best(personal_bests, "LapTimeFloat"),
                ],
            }
        }
        lap_time_styling = {
            "field": "Lap time",
            "cellStyle": {
                "styleConditions": [
                    conditional_styling.get_red_for_invalid(),
                    conditional_styling.get_purple_for_best(overall_bests, "LapTimeFloat"),
                    conditional_styling.get_green_for_personal_best(personal_bests, "LapTimeFloat"),
                ],
            }
        }
        sector_1_styling = {
            "field": "Secteur 1",
            "cellStyle": {
                "styleConditions": [
                    conditional_styling.get_red_for_invalid(),
                    conditional_styling.get_purple_for_best(overall_bests, "Secteur1Float"),
                    conditional_styling.get_green_for_personal_best(personal_bests, "Secteur1Float"),
                ],
            }
        }
        sector_2_styling = {
            "field": "Secteur 2",
            "cellStyle": {
                "styleConditions": [
                    red_for_invalid,
                    {
                        "condition": f"params.data.Secteur2Float == {overall_bests['Secteur2Float']}",
                        "style": {"backgroundColor": "purple", "color": "white"},
                    },
                    {
                        "condition": f"params.data.Secteur2Float == {personal_bests['Secteur2Float']}",
                        "style": {"backgroundColor": "green", "color": "white"},
                    },
                ],
            }
        }
        sector_3_styling = {
            "field": "Secteur 3",
            "cellStyle": {
                "styleConditions": [
                    red_for_invalid,
                    {
                        "condition": f"params.data.Secteur3Float == {overall_bests['Secteur3Float']}",
                        "style": {"backgroundColor": "purple", "color": "white"},
                    },
                    {
                        "condition": f"params.data.Secteur3Float == {personal_bests['Secteur3Float']}",
                        "style": {"backgroundColor": "green", "color": "white"},
                    },
                ],
            }
        }

        grid = dash_ag_grid.AgGrid(
            id=driver+"lap-times",
            rowData=lap_times[lap_times["Driver"]==driver].to_dict("records"),
            columnDefs=[
                lap_number_styling,
                lap_time_styling,
                sector_1_styling,
                sector_2_styling,
                sector_3_styling,
            ],
            columnSize="sizeToFit",
            dashGridOptions={
                "rowSelection": {"mode": "multiRow"},
                "theme": {"function": "themeAlpine.withParams({backgroundColor: 'black' , foregroundColor: 'white', accentColor : 'lightblue'})"},
            },
            style = {"height": 520},
        )

        output.append(dash.html.H3(driver, style={"margin-top": "30px", "margin-left": "15px"}))
        output.append(grid)
    return output


def get_lap_times_comparison(info: dict, selected_laps: pandas.DataFrame) -> list:
    header = dash.html.H2("Analyse des tours sélectionnés", style={"margin-top": "30px", "margin-left": "30px"})
    if selected_laps.empty:
        return [header]
    try:
        any_driver = selected_laps["Driver"].unique()[0]
    except IndexError:
        return [header]

    sector_names = info[any_driver]["Sector times"].keys()
    drivers = selected_laps["Driver"].tolist()
    lap_numbers = selected_laps["Lap number"].tolist()
    column_names = dict()
    for index in range(len(selected_laps)):
        driver = drivers[index]
        lap_number = lap_numbers[index]
        column_names[index] = driver + ", Tour n°" + str(lap_number)
    selected_laps = selected_laps[sector_names].copy()
    selected_laps = selected_laps.transpose()
    selected_laps.rename(columns=column_names, inplace=True)
    selected_laps["Secteur"] = selected_laps.index
    grid = dash_ag_grid.AgGrid(
        id="lap-times-comparison",
        rowData=selected_laps.to_dict("records"),
        columnDefs=[
            {"field": "Secteur"},
            *[{"field": column_name} for column_name in column_names.values()],
        ],
        columnSize="sizeToFit",
        dashGridOptions={
            "rowSelection": {'mode': 'singleRow'},
            "theme": {"function": "themeAlpine.withParams({backgroundColor: 'black' , foregroundColor: 'white', accentColor : 'lightblue'})"},
        },
        style={"height": 640},
    )
    return [[header, grid]]



def plot_lap_times_graph(drivers: str, lap_times: pandas.DataFrame) -> plotly.graph_objects.Figure:
    figure = plotly.graph_objects.Figure()
    for driver in drivers:
        figure.add_trace(
            plotly.graph_objects.Scatter(
                x=lap_times[lap_times["Driver"]==driver]["Lap number"],
                y=pandas.to_datetime(lap_times[lap_times["Driver"]==driver]["LapTimeFloat"], unit="s"),
                mode='markers+lines',
                name=driver,
                marker=dict(
                    symbol=pandas.Series(
                        "arrow-up",
                        index=lap_times[lap_times["Driver"]==driver].index
                    ).mask(
                        lap_times[lap_times["Driver"]==driver]["IsValid"] == True,
                        "circle"
                    ),
                ),
            ),
        )
    figure.update_layout(
        title="Temps au tour",
        xaxis=dict(
            title=dict(text="Tour"),
        ),
        yaxis=dict(
            tickformat="%M:%S.%f",
            title=dict(text="Temps"),
        ),
        legend=dict(xanchor="right", yanchor="top"),
        template="plotly_dark",
    )
    return figure
