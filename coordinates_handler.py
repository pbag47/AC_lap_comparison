from numpy import sin, cos, atan2, deg2rad, sqrt, rad2deg
from PIL import Image
from typing import Literal, Self
import lat_lon_parser

import plotly


ALTITUDE = 254
EARTH_RADIUS = 6_371_000 + ALTITUDE


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

    def get_xy_from_lat_lon(self, origin: Self):
        self.x = EARTH_RADIUS * deg2rad(self.longitude - origin.longitude) * cos(deg2rad(origin.latitude))
        self.y = EARTH_RADIUS * deg2rad(self.latitude - origin.latitude)

    def get_lat_lon_from_xy(self, origin: Self):
        self.latitude = origin.latitude + rad2deg(self.y / EARTH_RADIUS)
        self.longitude = origin.longitude + rad2deg(self.x / EARTH_RADIUS) / cos(deg2rad(origin.latitude))


def cartesian_distance(p1: Coordinates, p2: Coordinates):
    return sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)


def gps_distance(p1: Coordinates, p2: Coordinates, altitude=254):
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


def get_offset_point(point: Coordinates, x_offset: float, y_offset: float) -> Coordinates:
    offset_point = Coordinates(x=point.x + x_offset,
                               y=point.y + y_offset,
                               z=point.z,
                               latitude=point.latitude + rad2deg(y_offset / EARTH_RADIUS),
                               longitude=point.longitude + rad2deg(x_offset / EARTH_RADIUS) / cos(deg2rad(point.latitude)))
    return offset_point


def get_origin(reference_points_file_name: str) -> tuple[Coordinates, Coordinates]:
    p1, p2 = get_reference_data(reference_points_file_name)
    origin1 = Coordinates(x=0, y=0, z=0)
    x_offset = dx(p1, origin1, method='cartesian')
    y_offset = dy(p1, origin1, method='cartesian')
    origin1 = get_offset_point(p1, x_offset, y_offset)
    origin2 = Coordinates(x=0, y=0, z=0)
    x_offset = dx(p2, origin2, method='cartesian')
    y_offset = dy(p2, origin2, method='cartesian')
    origin2 = get_offset_point(p2, x_offset, y_offset)

    error = gps_distance(origin1, origin2)
    print("Origin error:", error, "m")
    return origin1, origin2


def get_reference_data(file_name: str) -> tuple[Coordinates, Coordinates]:
    with open(file_name, 'r') as file:
        _ = file.readline()  # Header
        p1_data = file.readline().split()
        p2_data = file.readline().split()
    p1 = Coordinates(x=float(p1_data[0]),
               y=float(p1_data[1]),
               latitude=lat_lon_parser.parse(p1_data[2]),
               longitude=lat_lon_parser.parse(p1_data[3]))
    p2 = Coordinates(x=float(p2_data[0]),
               y=float(p2_data[1]),
               latitude=lat_lon_parser.parse(p2_data[2]),
               longitude=lat_lon_parser.parse(p2_data[3]))
    return p1, p2


def validation(file_name: str):
    p1, p2 = get_reference_data(file_name)
    d_cartesian = cartesian_distance(p1, p2)
    d_gps = gps_distance(p1, p2)
    print("Error:", abs(d_cartesian - d_gps), "m")


def image_plot(image_file_name: str, info):
    top_left = info[0]
    bottom_right = info[1]
    origin1 = info[2]
    origin2 = info[3]
    figure = plotly.graph_objects.Figure()
    with Image.open(image_file_name) as image:
        width = abs(dx(top_left, bottom_right, method='cartesian'))
        height = abs(dy(top_left, bottom_right, method='cartesian'))
        figure.add_layout_image(
            x=top_left.x,
            y=bottom_right.y,
            sizex=width,
            sizey=height,
            xref="x",
            yref="y",
            opacity=1.0,
            layer="below",
            source=image,
            sizing='stretch',
            xanchor="left",
            yanchor="bottom",
        )
    figure.add_trace(plotly.graph_objects.Scatter(x=[origin1.x, origin2.x, top_left.x, bottom_right.x],
                                                  y=[origin1.y, origin2.y, top_left.y, bottom_right.y],))
    figure.update_yaxes(scaleanchor="x", scaleratio=1)
    figure.update_layout(template="plotly_dark")
    figure.show()


if __name__ == '__main__':
    validation("config/reference_points.txt")
    origin_point1, origin_point2 = get_origin("config/reference_points.txt")
    tl = Coordinates(latitude=lat_lon_parser.parse("36.583778°N"), longitude=lat_lon_parser.parse("121.758089°W"))
    tl.get_xy_from_lat_lon(origin_point1)
    br = Coordinates(latitude=lat_lon_parser.parse("36.582364°N"), longitude=lat_lon_parser.parse("121.756692°W"))
    br.get_xy_from_lat_lon(origin_point1)
    image_plot("config/sections/T1.png", [tl, br, origin_point1, origin_point2])
