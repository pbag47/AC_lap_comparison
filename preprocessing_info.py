
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


def get_laps(json_export_file: str) -> dict:
    with open(json_export_file) as json_file:
        data = json.load(json_file)
    laps = data['lapValid']
    lap_times = data['laptimes']
    for key, value in laps.items():
        laps[key] = (lap_times[int(key)-1], int(value))
    return laps


def save_as_json(info_dict: dict, driver_name: str, output_folder: str = "compressed_data") -> None:
    new_json_file_path = os.path.join(
        output_folder,
        driver_name + " - Laps.json"
    )
    with open(new_json_file_path, 'w') as json_file:
        json.dump(info_dict, json_file, indent=2)
    print(f"{new_json_file_path}: file saved")


def preprocessing_info(raw_data_file, json_export_file, output_folder="compressed_data") -> dict:
    info_dict = get_info(raw_data_file)
    laps = get_laps(json_export_file)
    info_dict["Laps"] = laps
    driver_name = info_dict["Driver"]
    save_as_json(
        info_dict,
        driver_name=driver_name,
        output_folder=output_folder
    )
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
