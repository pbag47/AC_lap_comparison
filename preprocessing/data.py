
import json
import numpy
import os
import pandas


def nan_helper(y):
    """Helper to handle indices and logical indices of NaNs.

    Input:
        - y, 1d numpy array with possible NaNs
    Output:
        - nans, logical indices of NaNs
        - index, a function, with signature indices= index(logical_indices),
          to convert logical indices of NaNs to 'equivalent' indices
    Example:
        >>> # linear interpolation of NaNs
        >>> nans, x= nan_helper(y)
        >>> y[nans]= numpy.interp(x(nans), x(~nans), y[~nans])
    """
    return numpy.isnan(y), lambda z: z.nonzero()[0]


def cleanup_headers(data: pandas.DataFrame) -> pandas.DataFrame:
    missing_labels = [key for key, _ in data.keys() if "Unnamed" in key]
    data = data.drop(labels=missing_labels, level=0, axis="columns")
    data = data.rename(columns=lambda x: " " if "Unnamed" in x else x, level=1)
    return data


def get_sample_rates(config_file_name: str = '../config/sample_rates.txt') -> dict:
    decoder = json.decoder.JSONDecoder()
    sample_rates = {}
    with open(config_file_name, 'r') as file:
        _ = file.readline()
        for line in file.readlines():
            title, sample_rate_str = line.split('|')
            title = title.rstrip()
            sample_rate_str = sample_rate_str.rstrip()
            sample_rates[title] = decoder.decode(sample_rate_str)
    return sample_rates


def resample_data(data: pandas.DataFrame, sample_rates: dict) -> pandas.DataFrame:
    new_data = pandas.DataFrame()
    for header in data.keys():
        name, unit = header
        try:
            data_series = data[name][unit].to_numpy().copy()
        except KeyError:
            data_series = data[name].to_numpy().copy()
            dataframe_to_append = pandas.DataFrame(data_series, columns=[name])
            new_data = pandas.concat([new_data, dataframe_to_append], axis="columns")
            continue
        if sample_rates[name] == 20:
            data_series = data_series[~numpy.isnan(data_series)]
            x = numpy.asarray(list(range(len(data_series))))
            new_x = numpy.asarray(list(range(2*len(data))))
            upsampled_data = numpy.interp(new_x/len(new_x), x/len(x), data_series)
            data_series = upsampled_data[::2]
        else:
            nans, x = nan_helper(data_series)
            data_series[nans] = numpy.interp(x(nans), x(~nans), data_series[~nans])
        dataframe_to_append = pandas.DataFrame(data_series, columns=[name])
        new_data = pandas.concat([new_data, dataframe_to_append], axis="columns")
    return new_data


def fix_coordinates(data: pandas.DataFrame) -> pandas.DataFrame:
    data["Car Coord X"] = - data["Car Coord X"]
    data["Car Coord Y"] = - data["Car Coord Y"]
    return data


def fix_rounding(data: pandas.DataFrame) -> pandas.DataFrame:
    integer_fields = [
        "Lap Invalidated",
        "Race Positon",
        "Num Tires Off Track",
        "DRS Available",
        "DRS Active",
        "ERS Is Charging",
        "ABS Active",
        "TC Active",
        "Lap Number",
        "Gear",
    ]
    for field in integer_fields:
        data[field] = round(data[field]).astype(int)
    return data


def fix_lap_number(data: pandas.DataFrame) -> pandas.DataFrame:
    lap_numbers = data["Lap Number"].to_numpy().copy()
    lap_numbers_diff = numpy.diff(lap_numbers)
    invalid_indices = numpy.where(lap_numbers_diff < 0)
    lap_numbers[invalid_indices[0] + 1] = lap_numbers[invalid_indices[0]]
    data["Lap Number"] = lap_numbers
    return data


def fix_car_pos_norm(info: dict, data: pandas.DataFrame) -> pandas.DataFrame:
    max_tolerated_speed = 400   # km/h
    track_length_str, _ = info["Venue Length"].split(" ")
    track_length = json.decoder.JSONDecoder().decode(track_length_str) / 1_000  # km
    max_car_speed_norm = max_tolerated_speed / (3_600 * track_length)
    lap_numbers = data["Lap Number"].unique()
    car_pos_norm_series = []
    for lap_number in lap_numbers:
        lap_data = data[data["Lap Number"] == lap_number]
        car_pos_norm = lap_data["Car Pos Norm"].to_numpy().copy()
        time = lap_data["time"].to_numpy()
        car_pos_norm[0] = 0.0
        last_valid_pos_norm = car_pos_norm[0]
        last_valid_time = time[0]
        for sample_index in range(len(car_pos_norm) - 1):
            speed_norm = (car_pos_norm[sample_index+1] - last_valid_pos_norm) / (time[sample_index+1] - last_valid_time)
            if speed_norm > max_car_speed_norm or speed_norm < 0 or car_pos_norm[sample_index+1] < 0:
                car_pos_norm[sample_index+1] = numpy.nan
            else:
                last_valid_pos_norm = car_pos_norm[sample_index+1]
                last_valid_time = time[sample_index+1]
        car_pos_norm[-1] = 1.0
        nans, x = nan_helper(car_pos_norm)
        car_pos_norm[nans] = numpy.interp(x(nans), x(~nans), car_pos_norm[~nans])
        car_pos_norm_series.append(car_pos_norm)
    fixed_series = numpy.concatenate(car_pos_norm_series)
    data["Car Pos Norm"] = fixed_series
    return data


def preprocessing_data(raw_data_file: str) -> pandas.DataFrame:
    sample_rates = get_sample_rates()
    df = pandas.read_csv(
        raw_data_file,
        skiprows=19,
        header=[0, 1],
    )
    df = cleanup_headers(df)
    # matplotlib.pyplot.plot(df["Car Pos Norm"], marker=11)
    # matplotlib.pyplot.show()
    print(df[["time", "Car Pos Norm"]])
    df = resample_data(df, sample_rates)
    print(df[["time", "Car Pos Norm"]])
    # matplotlib.pyplot.plot(df["Car Pos Norm"], marker=11)
    # matplotlib.pyplot.show()
    df = fix_rounding(df)
    df = fix_lap_number(df)
    df = fix_coordinates(df)
    return df


def preprocessing_test():
    raw_data_file = os.path.join(
        "../raw_data",
        "corvette_c7_laguna_seca_example.csv"
    )
    df = preprocessing_data(raw_data_file)
    print(df)


def read_test():
    df = pandas.read_csv(
        os.path.join(
            "../compressed_data",
            "compressed_test.csv.gz",
        ),
        index_col=0,
    )
    print(df.keys().tolist())


if __name__ == "__main__":
    # read_test()
    preprocessing_test()
