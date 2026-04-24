

default_figure_height = 250
default_figure_margins = dict(
    # l=10,
    # r=10,
    t=40,
    b=40,
)
figure_template = "plotly_dark"


track_map_layout = dict(
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False),
    # margin=dict(l=10, r=10, t=30, b=20),
    title=dict(text="Trajectoire"),
    legend=dict(xanchor="right", yanchor="top"),
    # width=600,
    height=600,
    template=figure_template,
    # template="SUPERHERO",
)

gg_diagram_layout = dict(
    xaxis=dict(
        title=dict(text="Accélération latérale (G)"),
        range=[-2, 2],
    ),
    yaxis=dict(
        scaleanchor="x",
        scaleratio=1,
        title=dict(text="Accélération longitudinale (G)"),
        autorange="reversed",
        range=[-2, 2],
    ),
    # margin=dict(l=10, r=10, t=30, b=20),
    title=dict(text="Diagramme G-G"),
    legend=dict(xanchor="right", yanchor="top"),
    # width=600,
    # height=450,
    template=figure_template,
)

throttle_layout = dict(
    xaxis=dict(title="Distance (% du tour)"),
    yaxis=dict(range=[0, 100]),
    height=default_figure_height,
    margin=default_figure_margins,
    title=dict(text="Accélérateur (%)"),
    legend=dict(xanchor="right", yanchor="top"),
    # template="SUPERHERO",
    template=figure_template,
)

brakes_layout = dict(
    xaxis=dict(title="Distance (% du tour)"),
    yaxis=dict(range=[0, 100]),
    height=default_figure_height,
    margin=default_figure_margins,
    title=dict(text="Frein (%)"),
    legend=dict(xanchor="right", yanchor="top"),
    # template="SUPERHERO",
    template=figure_template,
)

steering_layout = dict(
    xaxis=dict(title="Distance (% du tour)"),
    height=default_figure_height,
    margin=default_figure_margins,
    title=dict(text="Angle au volant (°)"),
    legend=dict(xanchor="right", yanchor="top"),
    # template="SUPERHERO",
    template=figure_template,
)

speed_layout = dict(
    xaxis=dict(title="Distance (% du tour)"),
    height=default_figure_height,
    margin=default_figure_margins,
    title=dict(text="Vitesse (km/h)"),
    legend=dict(xanchor="right", yanchor="top"),
    # template="SUPERHERO",
    template=figure_template,
)


def apply(track_map_figure, gg_diagram_figure, throttle_figure, brakes_figure, steering_figure, speed_figure):
    track_map_figure.update_layout(track_map_layout)
    gg_diagram_figure.update_layout(gg_diagram_layout)
    throttle_figure.update_layout(throttle_layout)
    brakes_figure.update_layout(brakes_layout)
    steering_figure.update_layout(steering_layout)
    speed_figure.update_layout(speed_layout)


