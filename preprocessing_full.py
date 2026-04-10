
import os

from preprocessing_data import preprocessing_data
from preprocessing_info import preprocessing_info


def preprocessing(raw_data_file, json_export_file):
    info_dict = preprocessing_info(raw_data_file, json_export_file)
    print(info_dict)
    driver_name = info_dict["Driver"]
    df = preprocessing_data(raw_data_file, driver_name=driver_name)
    print(df)


def main():
    raw_csv_file = os.path.join(
        "raw_data",
        "corvette_c7_laguna_seca_example.csv"
    )
    json_file = os.path.join(
        "json_data",
        "1751654595-Chuck-8(106.737).json"
    )
    preprocessing(raw_csv_file, json_file)


if __name__ == '__main__':
    main()
