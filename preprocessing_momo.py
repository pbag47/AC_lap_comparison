
import json
import numpy
import os
import pandas

from preprocessing_info import get_laps
from preprocessing_full import get_sectors, save_as_json, save_as_compressed_csv



def preprocessing_info_momo():
    json_export_file = os.path.join("json_data", "1775762035-momolafriteuz-11(145.956).json")
    copied_file = os.path.join("compressed_data", "Piotr - Info.json")
    with open(json_export_file) as json_file:
        info = json.load(json_file)
    with open(copied_file) as json_file:
        copied_info = json.load(json_file)
    new_info = copied_info.copy()
    lap_times, laps_valid = get_laps(json_export_file)
    sector_times = dict()
    sectors = get_sectors()
    for sector_name in sectors.keys():
        sector_times[sector_name] = dict()
    for lap_number_str in info["laps"].keys():
        for sector_name in sectors.keys():
            sector_times[sector_name][lap_number_str] = numpy.nan
        sector_times["Tour complet"][lap_number_str] = lap_times[int(lap_number_str)]
    new_info["Driver"] = "momolafriteuz"
    new_info["Lap times"] = lap_times
    new_info["Laps valid"] = laps_valid
    new_info["Sector times"] = sector_times
    print(new_info)
    return new_info


def generate_empty_dataframe(column_names: list[str]) -> pandas.DataFrame:
    df = pandas.DataFrame(columns=column_names)
    return df


def get_data_fields():
    fields_index = os.path.join("config", "fields.txt")
    with open(fields_index) as file:
        fields = file.readlines()
    filtered_fields = []
    for field in fields:
        if field == "\n": continue
        head, _, _ = field.partition('(')
        filtered_fields.append(head.strip())
    return filtered_fields


if __name__ == "__main__":
    output_folder = "compressed_data"
    info_dict = preprocessing_info_momo()
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
