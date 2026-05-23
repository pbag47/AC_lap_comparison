import pandas as pd
import dash
from dash import html


def build_podium(df: pd.DataFrame | None) -> html.Div:
    if df is None:
        return html.Div()

    df = df.sort_values("Ranking").reset_index(drop=True)
    colors = {
        "bg":        "transparent",
        "1":         "#FFD700",
        "2":         "#C0C0C0",
        "3":         "#CD7F32",
        "rest":      "#4FC3F7",
        "text_main": "#E8F4FD",
        "text_dim":  "#7EB8D4",
        "divider":   "rgba(78, 195, 247, 0.18)",
        "card_bg":   "rgba(0, 20, 40, 0.55)",
    }
    medal_label = {1: "🥇", 2: "🥈", 3: "🥉"}
    step_heights = {1: "190px", 2: "145px", 3: "110px"}
    delays = {1: "0.1s", 2: "0.25s", 3: "0.4s"}

    podium_rows = df[df["Ranking"] <= 3]
    podium_blocks = []

    # P2 | P1 | P3
    order = [2, 1, 3]
    for rank in order:
        row = podium_rows[podium_rows["Ranking"] == rank]
        if row.empty:
            podium_blocks.append(html.Div(style={"flex": "1"}))
            continue
        row = row.iloc[0]
        color = colors.get(str(rank))
        block = html.Div(
            [
                html.Div(
                    [
                        html.Div(medal_label.get(rank), className="podium-medal"),
                        html.Div(
                            row["Driver"],
                            className="podium-name",
                            style={"color": color}
                        ),
                        html.Div(row["Lap time"], className="podium-time"),
                    ],
                    className="podium-info"
                ),
                html.Div(
                    html.Span(
                        str(rank),
                        className="podium-rank-num",
                        style={"color": color}
                    ),
                    className="podium-step",
                    style={
                        "height": step_heights[rank],
                        "background": f"linear-gradient(180deg, {color}22 0%, {color}08 100%)",
                        "border-top": f"3px solid {color}",
                    }
                ),
            ],
            className=f"podium-block podium-block--{rank}",
            style={"animation-delay": delays.get(rank)}
        )
        podium_blocks.append(block)

    # P4+
    rest_rows = df[df["Ranking"] > 3].sort_values("Ranking")
    ranking_items = []
    if not rest_rows.empty:
        ranking_items.append(
            html.Div("Classement", className="ranking-section-label")
        )
        for i, (_, row) in enumerate(rest_rows.iterrows()):
            ranking_items.append(
                html.Div(
                    [
                        html.Span(f"P{row['Ranking']}", className="ranking-pos"),
                        html.Span(row["Driver"], className="ranking-driver"),
                        html.Span(row["Lap time"], className="ranking-time"),
                    ],
                    className="ranking-row",
                    style={"animation-delay": f"{0.5 + i * 0.1}s"}
                )
            )

    return html.Div(
        [
            html.Div("Classement final · Meilleur tour", className="podium-title"),
            html.Div(podium_blocks, className="podium-stage"),
            html.Div(className="podium-baseline"),
            html.Div(ranking_items, className="ranking-table") if ranking_items else None,
        ],
        className="podium-root",
        style={
            "background": colors["card_bg"],
            "border-radius": "12px",
            "border": f"1px solid {colors['divider']}",
            "backdrop-filter": "blur(12px)"
        }
    )


if __name__ == "__main__":
    sample_data = pd.DataFrame([
        {"Driver": "First driver", "Lap time": "1:42.384", "Ranking": 1},
        {"Driver": "Second driver", "Lap time": "1:43.017", "Ranking": 2},
        {"Driver": "Third driver", "Lap time": "1:43.591", "Ranking": 3},
        {"Driver": "Fourth driver", "Lap time": "1:44.102", "Ranking": 4},
        {"Driver": "Fifth driver", "Lap time": "1:44.889", "Ranking": 5},
        {"Driver": "Sixth driver", "Lap time": "1:45.203", "Ranking": 6},
    ])

    app = dash.Dash(__name__)
    app.layout = html.Div(
        build_podium(sample_data),
        style={
            "min-height": "100vh",
            "background": "linear-gradient(135deg, #020c1b 0%, #0a1628 60%, #050e1a 100%)",
            "display": "flex",
            "align-items": "center",
            "justify-content": "center",
            "padding": "40px 16px",
            "box-sizing": "border-box",
        }
    )
    app.run(debug=True)
