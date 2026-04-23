
import os
import matplotlib.pyplot
import numpy
import pandas

from preprocessing_info import preprocessing_info
from preprocessing_data import cleanup_headers, fix_coordinates, fix_lap_number, fix_rounding, resample_data, get_sample_rates
from preprocessing_full import fix_car_pos_norm, get_sector_times, get_sectors, save_as_json, save_as_compressed_csv


def preprocessing(raw_data_file, json_export_file) -> (dict, pandas.DataFrame):
    info_dict = preprocessing_info(raw_data_file, json_export_file)
    if len(info_dict["Lap times"].keys()) == 1:
        new_dict = {}
        for key, value in info_dict["Lap times"].items():
            new_dict[key+11] = value
        info_dict["Lap times"] = new_dict
    if len(info_dict["Laps valid"].keys()) == 1:
        new_dict = {}
        for key, value in info_dict["Laps valid"].items():
            new_dict[key + 11] = value
        info_dict["Laps valid"] = new_dict
    df = preprocessing_data(raw_data_file)
    df = fix_car_pos_norm(info_dict, df)
    sectors = get_sectors()
    sector_times = get_sector_times(info_dict, df, sectors)
    info_dict["Sector times"] = sector_times
    return info_dict, df


def merge_json_dicts(first_json_dict, second_json_dict) -> dict:
    merged_json_dict = first_json_dict.copy()
    merged_json_dict["Lap times"] = first_json_dict["Lap times"] | second_json_dict["Lap times"]
    merged_json_dict["Laps valid"] = first_json_dict["Laps valid"] | second_json_dict["Laps valid"]
    for sector_name in merged_json_dict["Sector times"].keys():
        merged_json_dict["Sector times"][sector_name] = first_json_dict["Sector times"][sector_name] | second_json_dict["Sector times"][sector_name]
    return merged_json_dict


def preprocessing_data(raw_data_file: str) -> pandas.DataFrame:
    sample_rates = get_sample_rates()
    df = pandas.read_csv(
        raw_data_file,
        skiprows=19,
        header=[0, 1],
    )
    df = cleanup_headers(df)
    df = resample_car_pos_norm(df)
    df = resample_data(df, sample_rates)
    df = fix_rounding(df)
    df = fix_lap_number(df)
    df = fix_coordinates(df)
    return df


def resample_car_pos_norm(data: pandas.DataFrame) -> pandas.DataFrame:
    data_series = data["Car Pos Norm"][" "].to_numpy().copy()
    data_series = data_series[~numpy.isnan(data_series)]
    x = numpy.asarray(list(range(len(data_series))))
    new_x = numpy.asarray(list(range(round(len(data)))))
    upsampled_data = numpy.interp(new_x/len(new_x), x/len(x), data_series)
    data.drop(columns=["Car Pos Norm"], inplace=True)
    data["Car Pos Norm"] = upsampled_data
    return data


def main():
    first_raw_csv_file = os.path.join(
        "raw_data",
        "17042026-200819-toty-ks_audi_a1s1-ks_laguna_seca.csv"
    )
    first_json_file = os.path.join(
        "json_data",
        "1776449299-toty-10(158.03).json"
    )
    second_raw_csv_file = os.path.join(
        "raw_data",
        "17042026-204207-toty-ks_audi_a1s1-ks_laguna_seca.csv"
    )
    second_json_file = os.path.join(
        "json_data",
        "1776451327-toty-1(142.22).json"
    )
    output_folder = "compressed_data"
    first_info_dict, first_data = preprocessing(first_raw_csv_file, first_json_file)
    second_info_dict, second_data = preprocessing(second_raw_csv_file, second_json_file)

    # print(first_data["Car Pos Norm"])
    # print(second_data)
    print(first_info_dict)
    print(second_info_dict)
    info_dict = merge_json_dicts(first_info_dict, second_info_dict)
    print(info_dict)

    # print(second_data)
    print(second_data["Lap Number"].unique())
    second_data = second_data[second_data["Lap Number"] == 12]
    # print(second_data)
    data = pandas.concat([first_data, second_data], axis="rows")
    # print(data)

    # matplotlib.pyplot.plot(first_data["time"], first_data["Car Pos Norm"])
    # matplotlib.pyplot.show()
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


def test():
    from data_import import import_data
    data = import_data("compressed_data", ["Chuck"])
    matplotlib.pyplot.plot(data["Car Pos Norm"], marker=11)
    matplotlib.pyplot.show()
    print(data)


if __name__ == "__main__":
    main()
