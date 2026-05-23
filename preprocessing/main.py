
import json
import os

import numpy
import pandas

from coordinates_handler import get_sections_from_ini_file
from paths import ROOT_PATH
from preprocessing.data import preprocessing_data, fix_car_pos_norm
from preprocessing.info import preprocessing_info


def get_sectors() -> dict:
    sections = get_sections_from_ini_file()
    sectors = {}
    for section in sections:
        sectors[section.title] = [section.start, section.stop]
    return sectors


def get_sector_times(info: dict, data: pandas.DataFrame, sectors: dict) -> dict:
    sectors_times = {}
    # section_indices = {}
    for sector_name, sector_bounds in sectors.items():
        sectors_times[sector_name] = {}
        for lap_number in info["Lap times"].keys():
            lap_data = data[data["Lap Number"] == lap_number]
            # section_indices[lap_number] = {}
            sector_time = lap_data[(sector_bounds[0] < lap_data["Car Pos Norm"]) & (lap_data["Car Pos Norm"] < sector_bounds[1])]["time"]
            # sector_indices = lap_data.index[(sector_bounds[0] < lap_data["Car Pos Norm"]) & (lap_data["Car Pos Norm"] < sector_bounds[1])]
            # print(sector_indices[0], sector_indices[-1])
            # section_indices[lap_number][]
            # print(lap_number, sector_name, sector_time)
            try:
                sector_end_time = sector_time.iloc[-1]
                sector_start_time = sector_time.iloc[0]
                sectors_times[sector_name][lap_number] = sector_end_time - sector_start_time
            except IndexError:
                sectors_times[sector_name][lap_number] = numpy.nan
    return sectors_times


def save_as_json(info_dict: dict, driver_name: str, output_folder: str | None = None) -> None:
    if output_folder is None:
        output_folder = os.path.join(ROOT_PATH, "compressed_data")
    new_json_file_path = os.path.join(
        output_folder,
        driver_name + " - Info.json"
    )
    with open(new_json_file_path, 'w') as json_file:
        json.dump(info_dict, json_file, indent=2)
    print(f"{new_json_file_path}: file saved")


def save_as_compressed_csv(data: pandas.DataFrame, driver_name: str, output_folder: str | None = None) -> None:
    if output_folder is None:
        output_folder = os.path.join(ROOT_PATH, "compressed_data")
    new_file_path = os.path.join(
        output_folder,
        driver_name + " - Data.csv.gz",
    )
    data.to_csv(
        new_file_path,
        compression="gzip",
    )
    print(f"{new_file_path}: file saved")


def preprocessing(raw_data_file, json_export_file) -> (dict, pandas.DataFrame):
    info_dict = preprocessing_info(raw_data_file, json_export_file)
    df = preprocessing_data(raw_data_file)
    df = fix_car_pos_norm(info_dict, df)
    sectors = get_sectors()
    sector_times = get_sector_times(info_dict, df, sectors)
    info_dict["Sector times"] = sector_times
    return info_dict, df


def main():
    raw_csv_file = os.path.join(
        ROOT_PATH,
        "raw_data",
        "19052026-183041-momolafriteuz_2-ks_audi_a1s1-ks_laguna_seca.csv"
    )
    json_file = os.path.join(
        ROOT_PATH,
        "json_data",
        "1779208241-momolafriteuz_2-11(137.616).json"
    )
    output_folder = os.path.join(ROOT_PATH, "compressed_data")
    info_dict, data = preprocessing(raw_csv_file, json_file)
    print(info_dict)
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


if __name__ == '__main__':
    main()
