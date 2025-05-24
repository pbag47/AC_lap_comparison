import csv
import json
import plotly.graph_objects
import re


class InfoField:
    def __init__(self, title: str, unit: str, value: float | int | bool | str | None):
        self.title = title
        self.unit = unit
        self.value = value

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
        self.indices: list[int] = []
        self.values: list[int | float | bool] = []
        self.get_indices(values_str)

    def get_indices(self, values_str: list[str]):
        for i in range(len(values_str)):
            try:
                value = json.decoder.JSONDecoder().decode(values_str[i])
                self.indices.append(i)
                self.values.append(value)
            except json.decoder.JSONDecodeError:
                pass


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
    return header, info, data


def plot_trajectory(data):
    figure = plotly.graph_objects.Figure()
    figure.add_trace(plotly.graph_objects.Scatter3d(x=data.car_coord_x.values,
                                                    y=data.car_coord_y.values,
                                                    z=data.car_coord_z.values,)
                     )
    figure.update_layout(scene=dict(aspectmode='data',
                                    aspectratio=dict(x=1, y=1, z=1)
                                    ),
                         template="plotly_dark",
                         )
    figure.show()




if __name__ == '__main__':
    # source_file = 'data/corvette_c7_laguna_seca_example.csv'
    source_file = 'data/gps_calibration.csv'
    h, info_container, data_container = main(source_file)
    print(info_container)
    plot_trajectory(data_container)


