import csv
import json
import plotly
import plotly.graph_objects
import plotly.io
import plotly.subplots
import re
import numpy

from itertools import groupby

from coordinates_handler import Origin, plot_track_map


DEFAULT_SAMPLE_RATE = 30


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

    def get_channel_names(self):
        return [key for key in vars(self).keys()]

    def get_channel_titles(self):
        return [channel.title for _, channel in vars(self).items()]

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
                attribute.sample_rate = dict(default=default_sample_rate,
                                             current=decoder.decode(sample_rate_str))
                setattr(self, attribute_name, attribute)

    def get_time_scales(self) -> dict:
        time_scales = {}
        sample_rates = numpy.unique([field.sample_rate['current'] for _, field in vars(self).items()])
        max_time = self.time.values[-1]
        for sample_rate in sample_rates:
            time_scales[sample_rate] = numpy.arange(start=0, stop=max_time+0.1, step=1/sample_rate)
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
    current_time_indices = data.last_sector_time.indices
    local_time_values = time_scales[data.last_sector_time.sample_rate['current']][current_time_indices]
    default_time_indices = data.last_sector_time.convert_indices(current_time_indices, data.last_sector_time.sample_rate['current'], data.last_sector_time.sample_rate['default'])
    default_time_values = time_scales[data.last_sector_time.sample_rate['default']][default_time_indices]
    sectors = data.last_sector_time.values
    output_array = numpy.array([current_time_indices, local_time_values, default_time_values, sectors])
    return output_array


def plot_sector_times(sector_times_array: numpy.ndarray, figure: plotly.graph_objects.Figure):
    figure.add_trace(plotly.graph_objects.Scatter(x=sector_times_array[1, [i for i in range(sector_times_array.shape[1]) if i % 3 == 0]],
                                                  y=sector_times_array[3, [i for i in range(sector_times_array.shape[1]) if i % 3 == 0]],
                                                  name='Sector times 1, local indexing',
                                                  showlegend=True,
                                                  line=dict(shape='hv')
                                                  ),
                     )
    figure.add_trace(plotly.graph_objects.Scatter(x=sector_times_array[1, [i for i in range(sector_times_array.shape[1]) if i % 3 == 1]],
                                                  y=sector_times_array[3, [i for i in range(sector_times_array.shape[1]) if i % 3 == 1]],
                                                  name='Sector times 2, local indexing',
                                                  showlegend=True,
                                                  line=dict(shape='hv')
                                                  ),
                     )
    figure.add_trace(plotly.graph_objects.Scatter(x=sector_times_array[1, [i for i in range(sector_times_array.shape[1]) if i % 3 == 2]],
                                                  y=sector_times_array[3, [i for i in range(sector_times_array.shape[1]) if i % 3 == 2]],
                                                  name='Sector times 3, local indexing',
                                                  showlegend=True,
                                                  line=dict(shape='hv')
                                                  ),
                     )


def plot_car_pos_norm_vs_lap_distance(data: DataContainer, time_scales):
    figure = plotly.subplots.make_subplots(rows=3, cols=1)

    ld_default_time_indices = data.lap_distance.convert_indices(data.lap_distance.indices,
                                                                data.lap_distance.sample_rate['current'],
                                                                data.lap_distance.sample_rate['default'])
    cpn_default_time_indices = data.car_pos_norm.convert_indices(data.car_pos_norm.indices,
                                                                 data.car_pos_norm.sample_rate['current'],
                                                                 data.car_pos_norm.sample_rate['default'])

    default_time_indices = numpy.union1d(ld_default_time_indices, cpn_default_time_indices)
    time_indices = default_time_indices[default_time_indices < len(time_scales[data.lap_distance.sample_rate['default']])]
    time_values = time_scales[data.lap_distance.sample_rate['default']][time_indices]
    ld_values = data.lap_distance[(time_indices, data.lap_distance.sample_rate['default'])]
    cpn_values = data.car_pos_norm[(time_indices, data.car_pos_norm.sample_rate['default'])]
    lap_number_values = data.lap_number[(time_indices, data.lap_number.sample_rate['default'])]

    figure.add_trace(plotly.graph_objects.Scatter(x=time_values,
                                                  y=ld_values,
                                                  name='Lap distance vs time',
                                                  showlegend=True,
                                                  line=dict(shape='hv')
                                                  ),
                     row=1,
                     col=1,
                     )

    figure.add_trace(plotly.graph_objects.Scatter(
                            x=time_values,
                            y=cpn_values,
                            name='Car Pos Norm vs time',
                            showlegend=True,
                            line=dict(shape='hv')
                        ),
                        row=2,
                        col=1,
                    )
    figure.add_trace(plotly.graph_objects.Scatter(
                            x=time_values,
                            y=lap_number_values,
                            name='Lap number vs time',
                            showlegend=True,
                            line=dict(shape='hv')
                        ),
                        row=2,
                        col=1,
                    )

    figure.add_trace(plotly.graph_objects.Scatter(
                            x=numpy.arange(len(time_values)),
                            y=time_values,
                            name='Time indices',
                            showlegend=True,
                            line=dict(shape='hv')
                        ),
                        row=3,
                        col=1,
                    )

    figure.show()


def general_xy_plot(figure: plotly.graph_objects.Figure,
                    data: DataContainer,
                    x_channel_name: str,
                    y_channel_name: str):
    x_axis_data = getattr(data, x_channel_name)
    y_axis_data = getattr(data, y_channel_name)
    x_axis_time_indices = x_axis_data.convert_indices(x_axis_data.indices,
                                                      x_axis_data.sample_rate['current'],
                                                      x_axis_data.sample_rate['default'])
    y_axis_time_indices = y_axis_data.convert_indices(y_axis_data.indices,
                                                      y_axis_data.sample_rate['current'],
                                                      y_axis_data.sample_rate['default'])
    indices = numpy.union1d(x_axis_time_indices, y_axis_time_indices)
    x_values = x_axis_data[(indices, x_axis_data.sample_rate['default'])]
    y_values = y_axis_data[(indices, y_axis_data.sample_rate['default'])]
    figure.add_trace(plotly.graph_objects.Scatter(x=x_values,
                                                  y=y_values,
                                                  name=f'{y_axis_data.title} vs {x_axis_data.title}',
                                                  showlegend=True,
                                                  line=dict(shape='hv')
                                                  ),
                     )
    figure.update_layout(xaxis=dict(title=f'{x_axis_data.title} ({x_axis_data.unit})'),
                         yaxis=dict(title=f'{y_axis_data.title} ({y_axis_data.unit})',),)


def general_time_plot(figure: plotly.graph_objects.Figure,
                      data: DataContainer,
                      time_scales: dict,
                      y_channel_name: str):
    y_axis_data = getattr(data, y_channel_name)
    x_values = time_scales[y_axis_data.sample_rate['current']][y_axis_data.indices]
    y_values = y_axis_data.values
    figure.add_trace(plotly.graph_objects.Scatter(x=x_values,
                                                  y=y_values,
                                                  name=f'{y_axis_data.title} vs time',
                                                  showlegend=True,
                                                  line=dict(shape='hv')
                                                  ),
                     )
    figure.update_layout(xaxis=dict(title='Time (s)',),
                         yaxis=dict(title=f'{y_axis_data.title} ({y_axis_data.unit})',),)


# def get_lap_times(data):
#     pass

    # figure.add_trace(plotly.graph_objects.Scatter(x=[i for i in range(len(data.lap_time.values))],
    #                                               y=data.lap_time.values,
    #                                               )
    #                  )


def debug():
    source_file = 'data/corvette_c7_laguna_seca_example.csv'
    # source_file = 'data/gps_calibration.csv'
    # source_file = 'data/turn_in_out_calibration.csv'
    h, info_container, data_container = main(source_file)
    # print(info_container)
    Origin.setup("config/reference_points.txt")
    data_container.set_sample_rates()
    data_time_scales = data_container.get_time_scales()
    print(data_container)
    plot_car_pos_norm_vs_lap_distance(data_container, data_time_scales)

    return data_container, data_time_scales


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
    # plot_car_pos_norm_vs_lap_distance(data_container, data_time_scales)
    fig = plotly.graph_objects.Figure()
    # general_xy_plot(fig, data_container, x_channel_name='lap_distance', y_channel_name='tire_temp_middle_fl')
    general_time_plot(fig, data_container, data_time_scales, 'tire_temp_inner_fl')
    general_time_plot(fig, data_container, data_time_scales, 'tire_temp_middle_fl')
    general_time_plot(fig, data_container, data_time_scales, 'tire_temp_outer_fl')

    # # plot_track_map(fig)
    # # plot_trajectory(data_container, fig)
    # sector_times = get_sector_times(data_container, time_scales=data_time_scales)
    # plot_sector_times(sector_times, fig)
    # # plot_lap_times(data_container, fig)
    #
    fig.show()
