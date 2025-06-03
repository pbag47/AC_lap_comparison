import csv
import json
import plotly.graph_objects
import plotly.io
import re
import numpy

from itertools import groupby
from coordinates_handler import Origin, plot_track_map


plotly.io.renderers.default = 'browser'
plotly.io.templates.default = 'plotly_dark'


class InfoField:
    def __init__(self, title: str, unit: str, value: float | int | bool | str | None):
        self.title: str = title
        self.unit: str = unit
        self.value: float | int | bool | str | None = value

    def __str__(self):
        return f"{self.title}: {self.value}{self.unit}"


class InfoContainer:
    def __init__(self, titles, units, values):
        attributes_names, indices_to_delete = self._get_attributes_names(titles)
        field_values = self._get_values(values)
        indices_to_delete.sort(reverse=True)
        for index in indices_to_delete:
            del titles[index]
            del units[index]
            del field_values[index]
        if len(attributes_names) != len(titles) or len(attributes_names) != len(units) or len(attributes_names) != len(field_values):
            raise ImportError("Mismatch in number of columns for InfoContainer: " +
                              str(len(attributes_names)) + " attributes, " +
                              str(len(titles)) + " titles, " +
                              str(len(units)) + " units, " +
                              str(len(field_values)) + " values")
        for attribute_name, title, unit, value in zip(attributes_names, titles, units, field_values):
            setattr(self, attribute_name, InfoField(title, unit, value))

    def __str__(self):
        output_str = 'InfoContainer:'
        for attribute_name, attribute_value in vars(self).items():
            output_str += f"\n\t{attribute_value}"
        return output_str

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
    def __init__(self, title: str, unit: str, values_str: list[str], sample_rate: int = 1):
        self.title: str = title
        self.unit: str = unit
        self.indices: numpy.ndarray = numpy.ndarray(())
        self.values: numpy.ndarray = numpy.ndarray(())
        self.sample_rate: int = sample_rate
        self.get_indices(values_str)

    def get_indices(self, values_str: list[str]):
        values_list = []
        indices_list = []
        for i in range(len(values_str)):
            try:
                value = json.decoder.JSONDecoder().decode(values_str[i])
                indices_list.append(i)
                values_list.append(value)
            except json.decoder.JSONDecodeError:
                pass
        filtered_values_list = []
        filtered_indices_list = []
        counter = 0
        for value, group in groupby(values_list):
            filtered_values_list.append(value)
            filtered_indices_list.append(indices_list[counter])
            number_of_repetitions = len(list(group))
            counter += number_of_repetitions
        self.values = numpy.array(filtered_values_list)
        self.indices = numpy.array(filtered_indices_list)

    def __getitem__(self, requested_index):
        closest_available_index = numpy.searchsorted(self.indices, requested_index, side="left")
        return self.values[closest_available_index]

    def __str__(self):
        return f"{self.title}: [{len(self.values)} values @ {self.sample_rate}Hz], {self.unit}"


class DataContainer:
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
            raise ImportError("Mismatch in number of columns for DataContainer: " +
                              str(len(attributes_names)) + " attributes, " +
                              str(len(titles)) + " titles, " +
                              str(len(units)) + " units, " +
                              str(len(values)) + " values columns")
        for attribute_name, title, unit, value_column in zip(attributes_names, titles, units, values):
            setattr(self, attribute_name, DataField(title, unit, value_column))

    def set_sample_rates(self, config_file_name: str = 'config/sample_rates.txt'):
        with open(config_file_name, 'r') as file:
            _ = file.readline()
            for line in file.readlines():
                title, sample_rate_str = line.split('|')
                title = title.rstrip()
                sample_rate_str = sample_rate_str.rstrip()
                attribute_list = [(name, field) for name, field in vars(self).items() if field.title == title]
                attribute_name = attribute_list[0][0]
                attribute = attribute_list[0][1]
                attribute.sample_rate = json.decoder.JSONDecoder().decode(sample_rate_str)
                setattr(self, attribute_name, attribute)

    def get_time_scales(self) -> dict:
        time_scales = {}
        sample_rates = numpy.unique([field.sample_rate for _, field in vars(self).items()])
        max_time = self.time.values[-1]
        print(max_time)
        for sample_rate in sample_rates:
            time_scales[sample_rate] = numpy.arange(start=0, stop=max_time, step=1/sample_rate)
            print(len(time_scales[sample_rate]))
        return time_scales

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

    def __str__(self):
        output_str = 'DataContainer:'
        for attribute_name, attribute_value in vars(self).items():
            output_str += f"\n\t{attribute_value}"
        return output_str


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


def plot_3d_trajectory(data: DataContainer, figure):
    figure.add_trace(plotly.graph_objects.Scatter3d(x=data.car_coord_x.values,
                                                    y=data.car_coord_y.values,
                                                    z=data.car_coord_z.values,)
                     )
    figure.update_layout(scene=dict(aspectmode='data',
                                    aspectratio=dict(x=1, y=1, z=1)
                                    ),
                         )


def plot_trajectory(data: DataContainer, figure):
    figure.add_trace(plotly.graph_objects.Scatter(x=data.car_coord_x.values,
                                                  y=data.car_coord_y.values,
                                                  )
                     )
    figure.update_yaxes(scaleanchor="x", scaleratio=1)


def get_sector_times(data: DataContainer, time_scales: dict) -> numpy.ndarray:
    sample_rate = data.last_sector_time.sample_rate
    sector_time_indices = numpy.floor(data.last_sector_time.indices * sample_rate / data.time.sample_rate).astype(int)
    car_pos_norm_indices = numpy.floor(data.last_sector_time.indices * sample_rate / data.car_pos_norm.sample_rate).astype(int)
    output_array = numpy.array([data.last_sector_time.indices, time_scales[sample_rate][sector_time_indices], data.car_pos_norm[car_pos_norm_indices], data.last_sector_time.values])
    return output_array


def plot_sector_times(sector_times_array: numpy.ndarray, time_scales, figure: plotly.graph_objects.Figure):
    figure.add_trace(plotly.graph_objects.Scatter(x=sector_times_array[1, [i for i in range(sector_times_array.shape[1]) if i % 3 == 0]],
                                                  y=sector_times_array[3, [i for i in range(sector_times_array.shape[1]) if i % 3 == 0]],
                                                  name='Sector times 1, local time scale',
                                                  showlegend=True,
                                                  line=dict(shape='hv')
                                                  ),
                     )
    figure.add_trace(plotly.graph_objects.Scatter(x=sector_times_array[1, [i for i in range(sector_times_array.shape[1]) if i % 3 == 1]],
                                                  y=sector_times_array[3, [i for i in range(sector_times_array.shape[1]) if i % 3 == 1]],
                                                  name='Sector times 2, local time scale',
                                                  showlegend=True,
                                                  line=dict(shape='hv')
                                                  ),
                     )
    figure.add_trace(plotly.graph_objects.Scatter(x=sector_times_array[1, [i for i in range(sector_times_array.shape[1]) if i % 3 == 2]],
                                                  y=sector_times_array[3, [i for i in range(sector_times_array.shape[1]) if i % 3 == 2]],
                                                  name='Sector times 3, local time scale',
                                                  showlegend=True,
                                                  line=dict(shape='hv')
                                                  ),
                     )

    figure.add_trace(plotly.graph_objects.Scatter(x=time_scales[30][sector_times_array[0, [i for i in range(sector_times_array.shape[1]) if i % 3 == 0]].astype(int)],
                                                  y=sector_times_array[3, [i for i in range(sector_times_array.shape[1]) if i % 3 == 0]],
                                                  name='Sector times 1, global time scale',
                                                  showlegend=True,
                                                  line=dict(shape='hv')
                                                  ),
                     )
    figure.add_trace(plotly.graph_objects.Scatter(x=time_scales[30][sector_times_array[0, [i for i in range(sector_times_array.shape[1]) if i % 3 == 1]].astype(int)],
                                                  y=sector_times_array[3, [i for i in range(sector_times_array.shape[1]) if i % 3 == 1]],
                                                  name='Sector times 2, global time scale',
                                                  showlegend=True,
                                                  line=dict(shape='hv')
                                                  ),
                     )
    figure.add_trace(plotly.graph_objects.Scatter(x=time_scales[30][sector_times_array[0, [i for i in range(sector_times_array.shape[1]) if i % 3 == 2]].astype(int)],
                                                  y=sector_times_array[3, [i for i in range(sector_times_array.shape[1]) if i % 3 == 2]],
                                                  name='Sector times 3, global time scale',
                                                  showlegend=True,
                                                  line=dict(shape='hv')
                                                  ),
                     )


def get_lap_times(data):
    pass

    # figure.add_trace(plotly.graph_objects.Scatter(x=[i for i in range(len(data.lap_time.values))],
    #                                               y=data.lap_time.values,
    #                                               )
    #                  )


if __name__ == '__main__':
    source_file = 'data/corvette_c7_laguna_seca_example.csv'
    # source_file = 'data/gps_calibration.csv'
    # source_file = 'data/turn_in_out_calibration.csv'
    h, info_container, data_container = main(source_file)
    # print(info_container)
    Origin.setup("config/reference_points.txt")
    data_container.set_sample_rates()
    data_time_scales = data_container.get_time_scales()
    print(data_container)
    fig = plotly.graph_objects.Figure()
    # plot_track_map(fig)
    # plot_trajectory(data_container, fig)
    sector_times = get_sector_times(data_container, time_scales=data_time_scales)
    plot_sector_times(sector_times, data_time_scales, fig)
    # plot_lap_times(data_container, fig)

    fig.show()
