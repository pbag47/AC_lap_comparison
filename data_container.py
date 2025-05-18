
import csv
import json
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
        attributes_names = self._get_attributes_names(titles)
        field_values = self._get_values(values)
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
        index = 0
        for name in titles:
            name = name.replace(' ', '_')
            name = name.casefold()
            name = re.sub('[^0-9a-z_]', '', name)
            name = re.sub('^[^a-z_]+', '', name)
            if not name:
                name = 'additional_field_' + str(index)
                index += 1
            attributes_names.append(name)
        return attributes_names

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


class DataContainer:
    def __init__(self, titles, units, values):
        print(len(titles), len(units), len(values))


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
    return header, info




if __name__ == '__main__':
    source_file = 'data/corvette_c7_laguna_seca_example.csv'
    h, i = main(source_file)

    print(i)

