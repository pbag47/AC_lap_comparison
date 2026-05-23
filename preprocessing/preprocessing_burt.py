

import json
import numpy
import os
import pandas

from paths import ROOT_PATH
from preprocessing.main import get_sectors, save_as_json, save_as_compressed_csv


def preprocessing_info_burt():
    json_summary_file = os.path.join(ROOT_PATH, "json_data", "burt.json")
    copied_file = os.path.join(ROOT_PATH, "compressed_data", "Piotr - Info.json")
    with open(json_summary_file) as json_file:
        info = json.load(json_file)
    with open(copied_file) as json_file:
        copied_info = json.load(json_file)
    new_info = copied_info.copy()
    lap_times = dict()
    is_valid = dict()
    sector_times = dict()
    sectors = get_sectors()
    for sector_name in sectors.keys():
        sector_times[sector_name] = dict()
    for lap_dict in info["sessions"][0]["laps"]:
        lap_number_str = str(lap_dict["lap"])
        if lap_number_str == "0": continue
        if lap_dict["time"] == -1:
            is_valid[lap_number_str] = 0
            lap_times[lap_number_str] = sum(lap_dict["sectors"]) / 1_000
        else:
            is_valid[lap_number_str] = 1
            lap_times[lap_number_str] = lap_dict["time"] / 1_000
        for sector_name in sectors.keys():
            sector_times[sector_name][lap_number_str] = numpy.nan
        sector_times["Secteur 1"][lap_number_str] = lap_dict["sectors"][0] / 1_000
        sector_times["Secteur 2"][lap_number_str] = lap_dict["sectors"][1] / 1_000
        sector_times["Secteur 3"][lap_number_str] = lap_dict["sectors"][2] / 1_000
        sector_times["Tour complet"][lap_number_str] = lap_times[lap_number_str]
    new_info["Driver"] = "burt"
    new_info["Lap times"] = lap_times
    new_info["Laps valid"] = is_valid
    new_info["Sector times"] = sector_times
    print(new_info)
    return new_info


def generate_empty_dataframe(column_names: list[str]) -> pandas.DataFrame:
    df = pandas.DataFrame(columns=column_names)
    return df


def get_data_fields():
    fields_index = os.path.join(ROOT_PATH, "config", "fields.txt")
    with open(fields_index) as file:
        fields = file.readlines()
    filtered_fields = []
    for field in fields:
        if field == "\n": continue
        head, _, _ = field.partition('(')
        filtered_fields.append(head.strip())
    return filtered_fields



if __name__ == '__main__':
    output_folder = os.path.join(ROOT_PATH, "compressed_data")
    info_dict = preprocessing_info_burt()
    data_fields = get_data_fields()
    data = generate_empty_dataframe(data_fields)
    driver_name = info_dict["Driver"]
    save_as_json(
        info_dict,
        driver_name=driver_name,
        output_folder=output_folder
    )
    save_as_compressed_csv(
        data,
        driver_name=driver_name,
        output_folder=output_folder
    )


