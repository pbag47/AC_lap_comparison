
import pandas


def get_red_for_invalid() -> dict:
    return {
        "condition": "params.data.IsValid < 0.5",
        "style": {"backgroundColor": "red", "color": "white"},
    }


def get_purple_for_best(overall_bests: pandas.DataFrame, target_column: str) -> dict:
    return {
        "condition": f"params.data.{target_column} == {overall_bests[target_column]}",
        "style": {"backgroundColor": "purple", "color": "white"},
    }

def get_green_for_personal_best(personal_bests: pandas.DataFrame, target_column: str) -> dict:
    return {
        "condition": f"params.data.{target_column} == {personal_bests[target_column]}",
        "style": {"backgroundColor": "green", "color": "white"},
    }