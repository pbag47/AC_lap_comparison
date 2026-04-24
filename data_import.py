
import json
import numpy
import os
import pandas



def parse_index(data_files_path: str, index_file_name: str = "index.txt") -> list[str]:
    index_file_path = os.path.join(data_files_path, index_file_name)
    with open(index_file_path, 'r') as file:
        lines = file.read().splitlines()

    drivers = []
    for line in lines:
        if not line: continue
        file_name, identifier = line.split("|")
        file_name = file_name.strip()
        if file_name == "index.txt": continue
        driver_name, content_type = file_name.split("-")
        driver_name = driver_name.strip()
        if driver_name not in drivers:
            drivers.append(driver_name)
    return drivers


def import_info(data_files_path: str, drivers: list[str]) -> dict:
    info = dict()
    for driver in drivers:
        info_file_path = os.path.join(data_files_path, driver + " - Info.json")
        with open(info_file_path, 'r') as file:
            info_dict = json.load(file)
        info[driver] = info_dict
    return info


def import_data(data_files_path: str, drivers: list[str]) -> pandas.DataFrame:
    data = pandas.DataFrame()
    for driver in drivers:
        data_file_path = os.path.join(data_files_path, driver + " - Data.csv.gz")
        df = pandas.read_csv(
            data_file_path,
            index_col=0,
        )
        df["Driver"] = driver
        data = pandas.concat([data, df])
    return data


def set_lap_tables(info: dict) -> pandas.DataFrame:
    lap_tables = pandas.DataFrame()
    for driver, session_info in info.items():
        lap_number_series = [int(lap_number_str) for lap_number_str in session_info["Lap times"].keys()]
        df = pandas.DataFrame({
            "Driver": driver,
            "Lap number": lap_number_series,
            "LapTimeFloat": session_info["Lap times"].values(),
            "Lap time": [seconds_to_time_str(time_float) for time_float in session_info["Lap times"].values()],
            "IsValid": session_info["Laps valid"].values(),
        })
        for sector_name in session_info["Sector times"].keys():
            sector_times = session_info["Sector times"][sector_name].values()
            df[sector_name.replace(" ", "") + "Float"] = sector_times
            df[sector_name] = [seconds_to_time_str(time_float) for time_float in sector_times]
        lap_tables = pandas.concat([lap_tables, df])
    return lap_tables



def seconds_to_time_str(time_in_seconds: float) -> str:
    if numpy.isnan(time_in_seconds):
        return str(time_in_seconds)
    minutes, seconds = divmod(time_in_seconds, 60)
    seconds, milliseconds = divmod(seconds, 1)
    if not minutes:
        return f"{int(seconds):02d}.{int(milliseconds*1_000):03d}"
    return f"{int(minutes):02d}:{int(seconds):02d}.{int(milliseconds*1_000):03d}"
