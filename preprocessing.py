import csv
import json
import os
from itertools import groupby

from data_container import DataContainer, InfoContainer, InfoField
from coordinates_handler import Origin
from Lap_class import Lap


def decimate_data(data: DataContainer):
    for data_field in data.get_channels_dict().values():
        if data_field.get_sample_rate() == 20:
            data_field.values = data_field.values[0:-1:2]
            data_field.index = data_field.indices[0:-1:2]  # Vérifier si /2 nécessaire
            data_field.sample_rate["current"] = int(data_field.get_sample_rate() / 2)


def fill_data_gaps(data: DataContainer):
    number_of_samples = len(data.time.values)
    for data_field in data.get_channels_dict().values():
        sample_rate_ratio = int(data_field.sample_rate["default"] / data_field.sample_rate["current"])
        if sample_rate_ratio != 1:
            filled_values = [entry for entry in data_field.values for _ in range(sample_rate_ratio)]
            if len(filled_values) != number_of_samples:
                extra_samples_number = number_of_samples - len(filled_values)
                for i in range(extra_samples_number):
                    filled_values.append(filled_values[-1])
                filled_values = filled_values[0:number_of_samples]
            filled_indices = [i for i in range(number_of_samples)]
            data_field.values = filled_values
            data_field.index = filled_indices
            data_field.sample_rate["current"] = data_field.sample_rate["default"]


def add_header_to_info(header: dict, info: InfoContainer):
    for attribute, value in header.items():
        attributes_name = InfoContainer._get_attributes_names([attribute])[0][0]
        setattr(info, attributes_name, InfoField(attribute, "", value))



def export_processed_data(info: InfoContainer, data: DataContainer):
    laps = get_laps(info, data)
    file_name = info.driver.value + " - Laps.json"
    with open(os.path.join("processed_data", file_name), "w") as json_file:
        json.dump(laps, json_file, indent=2, cls=Lap.Encoder)


def get_laps(info: InfoContainer, data: DataContainer) -> list[Lap]:
    number_of_sectors, _ = divmod(len(data.last_sector_time.values) - 1, 3)
    number_of_laps, _ = divmod(number_of_sectors, 3)
    laps = []
    start_index = 3
    step = 3
    sectors_per_lap = 3
    lap_index_counter = 0
    for lap_number, lap_group in groupby(data.lap_number.values):
        number_of_consecutive_values = len(list(lap_group))
        lap = Lap(
            number=lap_number,
            driver=info.driver.value,
            start_index=lap_index_counter,
        )
        sector_times = []
        for sector_time, sector_group in groupby(data.last_sector_time.values):
            sector_times.append(sector_time)
        sector_filter = slice(
            start_index + (step*sectors_per_lap*lap_number),
            start_index + (step*sectors_per_lap*(lap_number+1)),
            step
        )
        sector_times = sector_times[sector_filter]
        lap.set_times(sector_times)
        laps.append(lap)
        lap_index_counter += number_of_consecutive_values
    return laps


def main(data_file: str):
    with open(data_file, 'r') as csv_file:
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
        info = InfoContainer(titles, units, values)
        row = next(csv_reader)
        while not row:
            row = next(csv_reader)
        titles = row
        units = next(csv_reader)
        for i, row in enumerate(csv_reader):
            if i == 0:
                data = [[] for _ in range(len(row))]
            for j, col in enumerate(row):
                data[j].append(col)
        data = DataContainer(titles, units, data)

        # Invert x and y coordinates so x+ points towards east and y+ points towards north
        data.car_coord_x.values = - data.car_coord_x.values
        data.car_coord_y.values = - data.car_coord_y.values
    return header, info, data


if __name__ == '__main__':
    source_file = 'raw_data/corvette_c7_laguna_seca_example.csv'
    # source_file = 'raw_data/04072025-204315-Chuck-ks_audi_a1s1-ks_laguna_seca.csv'
    # source_file = 'raw_data/gps_calibration.csv'
    # source_file = 'raw_data/turn_in_out_calibration.csv'

    h, info_container, data_container = main(source_file)
    Origin.setup("config/reference_points.txt")
    data_container.set_sample_rates()
    decimate_data(data_container)
    fill_data_gaps(data_container)

    add_header_to_info(h, info_container)

    print(info_container)
    print(data_container)

    info_container.save_as_csv()
    export_processed_data(info_container, data_container)
    # TODO: Export DataContainer as csv file with unified sample rates
