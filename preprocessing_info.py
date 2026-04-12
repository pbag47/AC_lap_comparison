
import csv
import os
import json


def get_info(csv_export_file: str) -> dict:
    with open(csv_export_file, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        row = next(csv_reader)
        header = dict()
        while row:
            key, value = row
            header[key] = value
            row = next(csv_reader)
        while not row:
            row = next(csv_reader)
        titles = row
        units = next(csv_reader)
        values = next(csv_reader)
        shift = 0
        for index in range(len(titles)):
            value = values[index+shift] + f" {units[index]}"
            if ":" in value:
                shift += 1
            header[titles[index]] = value
        return header


def get_laps(json_export_file: str) -> (dict, dict):
    with open(json_export_file) as json_file:
        data = json.load(json_file)
    lap_valid = data['lapValid']
    lap_times = data['laptimes']
    laps_times = {}
    laps_valid = {}
    for key in lap_valid.keys():
        laps_times[int(key)] = lap_times[int(key)-1]
        laps_valid[int(key)] = int(lap_valid[key])
    return laps_times, laps_valid


def preprocessing_info(raw_data_file, json_export_file, output_folder="compressed_data") -> dict:
    info_dict = get_info(raw_data_file)
    lap_times, laps_valid = get_laps(json_export_file)
    info_dict["Lap times"] = lap_times
    info_dict["Laps valid"] = laps_valid
    return info_dict


def test() -> None:
    raw_data_file = os.path.join(
        "raw_data",
        "corvette_c7_laguna_seca_example.csv"
    )
    json_export_file = os.path.join(
        "json_data",
        "1751654595-Chuck-8(106.737).json"
    )
    info_dict = preprocessing_info(raw_data_file, json_export_file)
    print(info_dict)


if __name__ == '__main__':
    test()
