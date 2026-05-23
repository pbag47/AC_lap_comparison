import configparser
import lat_lon_parser
import os

from numpy import sin, cos, atan2, deg2rad, sqrt, rad2deg
from PIL import Image
from typing import Literal, Type

from paths import ROOT_PATH


ALTITUDE = 254
EARTH_RADIUS = 6_371_000 + ALTITUDE


class Origin:
    x = 0
    y = 0
    z = 0
    latitude = 0
    longitude = 0
    altitude = 0
    error = 0

    @classmethod
    def setup(cls, reference_points_file_name: str):
        p1, p2 = get_reference_data(reference_points_file_name)
        origin1 = Coordinates(x=0, y=0, z=0)
        origin1.latitude = p1.latitude - rad2deg(p1.y / EARTH_RADIUS)
        origin1.longitude = p1.longitude - rad2deg(p1.x / EARTH_RADIUS) / cos(deg2rad(p1.latitude))
        origin2 = Coordinates(x=0, y=0, z=0)
        origin2.latitude = p2.latitude - rad2deg(p2.y / EARTH_RADIUS)
        origin2.longitude = p2.longitude - rad2deg(p2.x / EARTH_RADIUS) / cos(deg2rad(p2.latitude))
        cls.error = gps_distance(origin1, origin2)

        # cls.latitude = origin1.latitude
        # cls.longitude = origin1.longitude
        cls.latitude = origin2.latitude
        cls.longitude = origin2.longitude


class Coordinates:
    def __init__(self,
                 x: float = 0.0,
                 y: float = 0.0,
                 z: float = 0.0,
                 latitude: float = 0.0,
                 longitude: float = 0.0):
        self.x = x
        self.y = y
        self.z = z
        self.latitude = latitude
        self.longitude = longitude

    def get_xy_from_lat_lon(self):
        self.x = EARTH_RADIUS * deg2rad(self.longitude - Origin.longitude) * cos(deg2rad(Origin.latitude))
        self.y = EARTH_RADIUS * deg2rad(self.latitude - Origin.latitude)

    def get_lat_lon_from_xy(self):
        self.latitude = Origin.latitude + rad2deg(self.y / EARTH_RADIUS)
        self.longitude = Origin.longitude + rad2deg(self.x / EARTH_RADIUS) / cos(deg2rad(Origin.latitude))


class Section:
    def __init__(self,
                 title: str,
                 start: float = 0.0,
                 stop: float = 0.0,
                 top_left: Coordinates | None = None,
                 bottom_right: Coordinates | None = None):
        self.title = title
        self.start = start
        self.stop = stop
        self.top_left = top_left
        self.bottom_right = bottom_right
        self.image = None

    def setup(self):
        if self.top_left is not None and self.bottom_right is not None:
            image_file_name = os.path.join(ROOT_PATH, "config", "sections", self.title + '.png')
            self.image = Image.open(image_file_name)
        else:
            self.image = None


def cartesian_distance(p1: Coordinates, p2: Coordinates):
    return sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)


def gps_distance(p1: Coordinates | Type[Origin], p2: Coordinates | Type[Origin]):
    latitude_difference = deg2rad(p1.latitude - p2.latitude)
    longitude_difference = deg2rad(p1.longitude - p2.longitude)
    a = ((sin(latitude_difference/2))**2 +
         cos(deg2rad(p1.latitude)) * cos(deg2rad(p2.latitude)) *
         (sin(longitude_difference/2))**2)
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return EARTH_RADIUS * c


def dx(p1: Coordinates, p2: Coordinates, method: Literal['cartesian', 'gps'] = 'cartesian') -> float:
    p1x = Coordinates(x=p1.x, longitude=p1.longitude)
    p2x = Coordinates(x=p2.x, longitude=p2.longitude)
    if method == 'cartesian':
        return p2.x - p1.x  # cartesian_distance(p1x, p2x)
    elif method == 'gps':
        return gps_distance(p1x, p2x)
    else:
        raise ValueError('Method must be either cartesian or gps')


def dy(p1: Coordinates, p2: Coordinates, method: Literal['cartesian', 'gps'] = 'cartesian') -> float:
    p1y = Coordinates(y=p1.y, latitude=p1.latitude)
    p2y = Coordinates(y=p2.y, latitude=p2.latitude)
    if method == 'cartesian':
        return p2.y - p1.y  # cartesian_distance(p1y, p2y)
    elif method == 'gps':
        return gps_distance(p1y, p2y)
    else:
        raise ValueError('Method must be either cartesian or gps')


def get_reference_data(file_name: str) -> tuple[Coordinates, Coordinates]:
    with open(file_name, 'r') as file:
        _ = file.readline()  # Header
        p1_data = file.readline().split()
        p2_data = file.readline().split()
    p1 = Coordinates(
        x=float(p1_data[0]),
        y=float(p1_data[1]),
        latitude=lat_lon_parser.parse(p1_data[2]),
        longitude=lat_lon_parser.parse(p1_data[3])
    )
    p2 = Coordinates(
        x=float(p2_data[0]),
        y=float(p2_data[1]),
        latitude=lat_lon_parser.parse(p2_data[2]),
        longitude=lat_lon_parser.parse(p2_data[3])
    )
    return p1, p2


def get_images_position(index_file_name: str | None = None) -> tuple:
    if index_file_name is None:
        index_file_name = os.path.join(ROOT_PATH, "config", "sections", "index.txt")
    with open(index_file_name, 'r') as file:
        _ = file.readline()
        name = []
        tl_lat = []
        tl_lon = []
        br_lat = []
        br_lon = []
        x_offset = []
        y_offset = []
        for line in file.readlines():
            results = line.split('|')
            name.append(results[0].rstrip())
            tl_lat.append(results[1].rstrip())
            tl_lon.append(results[2].rstrip())
            br_lat.append(results[3].rstrip())
            br_lon.append(results[4].rstrip())
            x_offset.append(results[5].rstrip())
            y_offset.append(results[6].rstrip())
        return name, tl_lat, tl_lon, br_lat, br_lon, x_offset, y_offset


def get_sections_from_ini_file(
        sections_folder_path: str | None = None,
        # ini_file_name: str = "config/sections/sections.ini"
    ) -> list[Section]:
    if sections_folder_path is None:
        sections_folder_path = os.path.join(ROOT_PATH, "config", "sections")
    sections_index_path = os.path.join(sections_folder_path, "index.txt")
    ini_file_name = os.path.join(sections_folder_path, "sections.ini")

    name, tl_lat, tl_lon, br_lat, br_lon, x_offset, y_offset = get_images_position(sections_index_path)
    config_parser = configparser.ConfigParser()
    config_parser.read(ini_file_name)
    sections_str = config_parser.sections()
    sections = []
    for section_str in sections_str:
        section = Section(
            title=config_parser[section_str]['TEXT'],
            start=float(config_parser[section_str]['IN']),
            stop=float(config_parser[section_str]['OUT']),
        )
        if section.title in name:
            index = name.index(section.title)
            top_left = Coordinates(
                latitude=lat_lon_parser.parse(tl_lat[index]),
                longitude=lat_lon_parser.parse(tl_lon[index])
            )
            top_left.get_xy_from_lat_lon()
            top_left.x += float(x_offset[index])
            top_left.y += float(y_offset[index])
            bottom_right = Coordinates(
                latitude=lat_lon_parser.parse(br_lat[index]),
                longitude=lat_lon_parser.parse(br_lon[index])
            )
            bottom_right.get_xy_from_lat_lon()
            bottom_right.x += float(x_offset[index])
            bottom_right.y += float(y_offset[index])
            section.top_left = top_left
            section.bottom_right = bottom_right
        section.setup()
        sections.append(section)
    return sections


def validation(file_name: str):
    p1, p2 = get_reference_data(file_name)
    d_cartesian = cartesian_distance(p1, p2)
    d_gps = gps_distance(p1, p2)
    print(f"Error between reference points: {abs(d_cartesian - d_gps): .3f} m")
    print(f"Origin GPS coordinates: {Origin.latitude: .3f}°N, {Origin.longitude: .3f}°E")
    print(f"Origin precision: {Origin.error: .3f} m")


if __name__ == '__main__':
    Origin.setup("config/reference_points.txt")
    validation("config/reference_points.txt")
