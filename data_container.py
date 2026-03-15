import csv
import json
import os
import re
import numpy


class Container:
    @staticmethod
    def _get_attributes_names(titles: list[str]):
        attributes_names = []
        indices_to_delete = []
        for i in range(len(titles)):
            name = titles[i]
            name = name.replace(' ', '_')
            name = name.casefold()
            name = re.sub('[^0-9a-z_]', '', name)
            name = re.sub('^[^a-z_]+', '', name)
            if not name:
                indices_to_delete.append(i)
                continue
            attributes_names.append(name)
        return attributes_names, indices_to_delete


class InfoField:
    def __init__(self, title: str, unit: str, value: float | int | bool | str | None):
        self.title: str = title
        self.unit: str = unit
        self.value: float | int | bool | str | None = value

    def __str__(self):
        return f"{self.title}: {self.value}{self.unit}"

    def as_csv_row(self) -> list[str]:
        return [self.title, str(self.value), self.unit]


class InfoContainer(Container):
    def __init__(self, titles, units, values):
        attributes_names, indices_to_delete = self._get_attributes_names(titles)
        field_values = self._get_values(values)
        indices_to_delete.sort(reverse=True)
        for index in indices_to_delete:
            del titles[index]
            del units[index]
            del field_values[index]
        if len(attributes_names) != len(titles) or len(attributes_names) != len(units) or len(attributes_names) != len(field_values):
            raise ImportError(
                "Mismatch in number of columns for InfoContainer: " +
                str(len(attributes_names)) + " attributes, " +
                str(len(titles)) + " titles, " +
                str(len(units)) + " units, " +
                str(len(field_values)) + " values"
            )
        for attribute_name, title, unit, value in zip(attributes_names, titles, units, field_values):
            setattr(self, attribute_name, InfoField(title, unit, value))

    def __str__(self):
        output_str = 'InfoContainer:'
        for attribute_name, attribute_value in vars(self).items():
            output_str += f"\n\t{attribute_value}"
        return output_str

    def save_as_csv(self):
        info_file_path = os.path.join("processed_data", self.driver.value + " - Info.csv")
        with open(info_file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for info_field in vars(self).values():
                writer.writerow(info_field.as_csv_row())

    @staticmethod
    def _get_values(values: list[str]):
        inferred_values = []
        for value in values:
            if not value:
                inferred_values.append(None)
                continue
            try:
                inferred_value = json.decoder.JSONDecoder().decode(value)
                inferred_values.append(inferred_value)
            except json.decoder.JSONDecodeError:
                if value.startswith(' '):
                    inferred_values[-1] = inferred_values[-1] + ',' + value
                else:
                    inferred_values.append(value)
        return inferred_values


class DataField:
    def __init__(self, title: str, unit: str, values_str: list[str], sample_rate: dict | None = None):
        self.title: str = title
        self.unit: str = unit
        self.indices: numpy.ndarray = numpy.ndarray(())  # Indexing based on current (local) sample rate
        self.values: numpy.ndarray = numpy.ndarray(())
        self.sample_rate: dict | None = sample_rate
        self.get_indices(values_str)

    def get_indices(self, values_str: list[str]):
        values_list = []
        indices_list = []
        counter = 0
        for i in range(len(values_str)):
            try:
                value = json.decoder.JSONDecoder().decode(values_str[i])
                indices_list.append(counter)
                values_list.append(value)
                counter += 1
            except json.decoder.JSONDecodeError:
                pass
        self.values = numpy.array(values_list)
        self.indices = numpy.array(indices_list)

    def get_sample_rate(self):
        return self.sample_rate["current"]

    def __getitem__(self, requested_index: tuple[int | slice, int]):
        if self.sample_rate is None:
            raise ValueError('Sample rate has not been set')
        indices, sample_rate_of_input_indices = requested_index
        corrected_indices = self.convert_indices(indices, sample_rate_of_input_indices, self.sample_rate['current'])
        closest_available_indices = numpy.searchsorted(self.indices, corrected_indices, side="right")
        return self.values[closest_available_indices-1]

    def __str__(self):
        if self.sample_rate is None:
            return f"{self.title}: [{len(self.values)} values @ undefined sample rate], {self.unit}"
        return f"{self.title}: [{len(self.values)} values @ {self.sample_rate['current']}Hz], {self.unit}"

    @staticmethod
    def convert_indices(indices: int | numpy.ndarray, current_sample_rate: int, new_sample_rate: int):
        new_indices = numpy.floor(indices * new_sample_rate / current_sample_rate).astype(int)
        return new_indices


class DataContainer(Container):
    def __init__(self, titles, units, values):
        attributes_names, indices_to_delete = self._get_attributes_names(titles)
        indices_to_delete.sort(reverse=True)
        for index in indices_to_delete:
            del titles[index]
            del units[index]
            try:
                del values[index]
            except IndexError:
                pass
        if len(attributes_names) != len(titles) or len(attributes_names) != len(units) or len(attributes_names) != len(values):
            raise ImportError(
                "Mismatch in number of columns for DataContainer: " +
                str(len(attributes_names)) + " attributes, " +
                str(len(titles)) + " titles, " +
                str(len(units)) + " units, " +
                str(len(values)) + " values columns"
            )
        for attribute_name, title, unit, value_column in zip(attributes_names, titles, units, values):
            setattr(self, attribute_name, DataField(title, unit, value_column))

    def get_channels_dict(self) -> dict[str: DataField]:
        return vars(self)

    def get_title_name_pairs(self):
        return [dict(label=channel.title, value=name) for name, channel in vars(self).items()]

    def set_sample_rates(self, config_file_name: str = 'config/sample_rates.txt'):
        decoder = json.decoder.JSONDecoder()
        with open(config_file_name, 'r') as file:
            header = file.readline()
            channel_header, sample_rate_header = header.split('|')
            sample_rate_header_text, default_sample_rate_str = sample_rate_header.split(':')
            default_sample_rate = decoder.decode(default_sample_rate_str)
            for line in file.readlines():
                title, sample_rate_str = line.split('|')
                title = title.rstrip()
                sample_rate_str = sample_rate_str.rstrip()
                attribute_list = [(name, field) for name, field in vars(self).items() if field.title == title]
                attribute_name = attribute_list[0][0]
                attribute = attribute_list[0][1]
                attribute.sample_rate = dict(
                    default=default_sample_rate,
                    current=decoder.decode(sample_rate_str)
                )
                setattr(self, attribute_name, attribute)

    def get_time_scales(self) -> dict:
        time_scales = {}
        sample_rates = numpy.unique([field.sample_rate['current'] for _, field in vars(self).items()])
        max_time = self.time.values[-1]
        for sample_rate in sample_rates:
            time_scales[sample_rate] = numpy.arange(start=0, stop=max_time+(1/(2*sample_rate)), step=1/sample_rate)
        return time_scales

    def save_as_csv(self, info: InfoContainer):
        data_file_path = os.path.join("processed_data", info.driver.value + " - Data.csv")
        with open(data_file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            header_row = [data_field.title for data_field in vars(self).values()]
            units_row = [data_field.unit for data_field in vars(self).values()]
            writer.writerow(header_row)
            writer.writerow(units_row)
            for row_number in range(len(self.time.values)):
                row = [data_field.values[row_number] for data_field in vars(self).values()]
                writer.writerow(row)

    def __str__(self):
        output_str = 'DataContainer:'
        for attribute_name, attribute_value in vars(self).items():
            output_str += f"\n\t{attribute_value}"
        return output_str


def import_raw_data(data_file: str):
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
    data.set_sample_rates()
    time_scales = data.get_time_scales()
    return header, info, data, time_scales


if __name__ == '__main__':
    # source_file = 'raw_data/corvette_c7_laguna_seca_example.csv'
    source_file = 'raw_data/04072025-204315-Chuck-ks_audi_a1s1-ks_laguna_seca.csv'
    # source_file = 'raw_data/gps_calibration.csv'
    # source_file = 'raw_data/turn_in_out_calibration.csv'
    h, info_container, data_container, data_time_scales = import_raw_data(source_file)
    print(h)
    print(info_container)
    print(data_container)

