
import os
import pandas
import scipy


def cleanup_headers(data: pandas.DataFrame) -> pandas.DataFrame:
    missing_labels = [key for key, _ in data.keys() if "Unnamed" in key]
    data = data.drop(labels=missing_labels, level=0, axis="columns")
    data = data.rename(columns=lambda x: " " if "Unnamed" in x else x, level=1)
    return data


def decimate_data(data: pandas.DataFrame) -> pandas.DataFrame:
    filtered_data = pandas.DataFrame()
    for header in data.keys():
        name, unit = header
        new_dataframe = data[data[name][unit].notnull()][name]
        new_dataframe.reset_index(drop=True, inplace=True)
        series = new_dataframe.to_numpy()
        resampled_data = pandas.DataFrame(scipy.signal.resample(series, len(data)))
        filtered_data = pandas.concat([filtered_data, resampled_data], axis="columns")
        filtered_data.rename(columns={0: name}, level=0, inplace=True)
    return filtered_data


def fix_coordinates(data: pandas.DataFrame) -> pandas.DataFrame:
    data["Car Coord X"] = - data["Car Coord X"]
    data["Car Coord Y"] = - data["Car Coord Y"]
    return data


def save_as_compressed_csv(data: pandas.DataFrame, driver_name: str, output_folder: str = "compressed_data") -> None:
    new_file_path = os.path.join(
        output_folder,
        driver_name + " - Data.csv.gz",
    )
    data.to_csv(
        new_file_path,
        compression="gzip",
    )
    print(f"{new_file_path}: file saved")


def preprocessing_data(raw_data_file: str, driver_name: str, output_folder: str = "compressed_data") -> pandas.DataFrame:
    df = pandas.read_csv(
        raw_data_file,
        skiprows=19,
        header=[0, 1],
    )
    df = cleanup_headers(df)
    df = decimate_data(df)
    df = fix_coordinates(df)
    save_as_compressed_csv(df, driver_name, output_folder)
    return df


def preprocessing_test():
    raw_data_file = os.path.join(
        "raw_data",
        "corvette_c7_laguna_seca_example.csv"
    )
    df = preprocessing_data(raw_data_file, "test")
    print(df)


def read_test():
    df = pandas.read_csv(
        os.path.join(
            "compressed_data",
            "compressed_test.csv.gz",
        ),
        index_col=0,
    )
    print(df.keys().tolist())


if __name__ == "__main__":
    read_test()
    # preprocessing_test()
