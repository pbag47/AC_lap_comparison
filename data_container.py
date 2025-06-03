import csv
import json
import plotly.graph_objects
import plotly.io
import re
import numpy

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
    def __init__(self, title: str, unit: str, values_str: list[str]):
        self.title: str = title
        self.unit: str = unit
        self.indices: numpy.ndarray = numpy.ndarray(())
        self.values: numpy.ndarray = numpy.ndarray(())
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
        self.values = numpy.array(values_list)
        self.indices = numpy.array(indices_list)

    def __getitem__(self, requested_index):
        closest_available_index = numpy.searchsorted(self.indices, requested_index, side="left")
        return self.values[closest_available_index]

    def __str__(self):
        return f"{self.title}: [{len(self.values)} values], {self.unit}"


class DataContainer:
    def __init__(self, titles, units, values):
        print(len(titles), len(units), len(values))
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


def plot_3d_trajectory(data, figure):
    figure.add_trace(plotly.graph_objects.Scatter3d(x=data.car_coord_x.values,
                                                    y=data.car_coord_y.values,
                                                    z=data.car_coord_z.values,)
                     )
    figure.update_layout(scene=dict(aspectmode='data',
                                    aspectratio=dict(x=1, y=1, z=1)
                                    ),
                         )


def plot_trajectory(data, figure):
    figure.add_trace(plotly.graph_objects.Scatter(x=data.car_coord_x.values,
                                                  y=data.car_coord_y.values,
                                                  )
                     )
    figure.update_yaxes(scaleanchor="x", scaleratio=1)


def get_sector_times(data: DataContainer) -> numpy.ndarray:
    values, local_indices = numpy.unique(data.last_sector_time.values, return_index=True)
    local_indices.sort()
    indices = data.last_sector_time.indices[local_indices]
    output_array = numpy.array([indices, data.time[indices], data.car_pos_norm[indices], data.last_sector_time[indices]])
    return output_array


def plot_sector_times(sector_times_array: numpy.ndarray, figure: plotly.graph_objects.Figure):
    figure.add_trace(plotly.graph_objects.Scatter(x=sector_times_array[1, [i for i in range(sector_times_array.shape[1]) if i % 3 == 0]],
                                                  y=sector_times_array[3, [i for i in range(sector_times_array.shape[1]) if i % 3 == 0]],
                                                  name='Sector times 1',
                                                  showlegend=True,
                                                  ),
                     )
    figure.add_trace(plotly.graph_objects.Scatter(x=sector_times_array[1, [i for i in range(sector_times_array.shape[1]) if i % 3 == 1]],
                                                  y=sector_times_array[3, [i for i in range(sector_times_array.shape[1]) if i % 3 == 1]],
                                                  name='Sector times 2',
                                                  showlegend=True,
                                                  ),
                     )
    figure.add_trace(plotly.graph_objects.Scatter(x=sector_times_array[1, [i for i in range(sector_times_array.shape[1]) if i % 3 == 2]],
                                                  y=sector_times_array[3, [i for i in range(sector_times_array.shape[1]) if i % 3 == 2]],
                                                  name='Sector times 3',
                                                  showlegend=True,
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
    print(info_container)
    Origin.setup("config/reference_points.txt")
    print(data_container)
    fig = plotly.graph_objects.Figure()
    # plot_track_map(fig)
    # plot_trajectory(data_container, fig)
    sector_times = get_sector_times(data_container)
    plot_sector_times(sector_times, fig)
    # plot_lap_times(data_container, fig)

    fig.show()


