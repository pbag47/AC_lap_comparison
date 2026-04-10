
import json
import os
import pandas
import scipy


def cleanup_headers(data: pandas.DataFrame) -> pandas.DataFrame:
    missing_labels = [key for key, _ in data.keys() if "Unnamed" in key]
    data = data.drop(labels=missing_labels, level=0, axis="columns")
    data = data.rename(columns=lambda x: " " if "Unnamed" in x else x, level=1)
    return data


def get_sample_rates(config_file_name: str = 'config/sample_rates.txt') -> dict:
    decoder = json.decoder.JSONDecoder()
    with open(config_file_name, 'r') as file:
        _ = file.readline()
        sample_rates = {}
        for line in file.readlines():
            title, sample_rate_str = line.split('|')
            title = title.rstrip()
            sample_rate_str = sample_rate_str.rstrip()
            sample_rates[title] = decoder.decode(sample_rate_str)
    return sample_rates


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


def main():
    raw_data_file = os.path.join(
        "raw_data",
        "corvette_c7_laguna_seca_example.csv"
    )
    df = pandas.read_csv(
        raw_data_file,
        skiprows=19,
        header=[0, 1],
    )
    df = cleanup_headers(df)
    df = decimate_data(df)
    print(df)
    df.to_csv(
        os.path.join(
            "compressed_data",
            "compressed_test.csv.gz",
        ),
        compression="gzip",
    )


def read_test():
    df = pandas.read_csv(
        os.path.join(
            "compressed_data",
            "compressed_test.csv.gz",
        ),
        index_col=0,
    )
    print(df)


if __name__ == "__main__":
    read_test()
    # main()
