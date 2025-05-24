from numpy import sin, cos, atan2, deg2rad, sqrt
import lat_lon_parser


class Coordinates:
    def __init__(self,
                 x: float = 0.0,
                 y: float = 0.0,
                 z: float = 0.0,
                 latitude: float = 0.0,
                 longitude: float = 0.0,
                 px: int = 0,
                 py: int = 0):
        self.x = x
        self.y = y
        self.z = z
        self.latitude = latitude
        self.longitude = longitude
        self.px = px
        self.py = py


def cartesian_distance(p1: Coordinates, p2: Coordinates):
    return sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)


def gps_distance(p1: Coordinates, p2: Coordinates, altitude=254):
    earth_radius = 6_371_000 + altitude
    latitude_difference = deg2rad(p1.latitude - p2.latitude)
    longitude_difference = deg2rad(p1.longitude - p2.longitude)
    a = ((sin(latitude_difference/2))**2 +
         cos(deg2rad(p1.latitude)) * cos(deg2rad(p2.latitude)) *
         (sin(longitude_difference/2))**2)
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return earth_radius * c


def get_reference_data(file_name: str) -> tuple[Coordinates, Coordinates]:
    with open(file_name, 'r') as file:
        _ = file.readline()  # Header
        p1_data = file.readline().split()
        p2_data = file.readline().split()
    p1 = Coordinates(x=float(p1_data[0]),
               y=float(p1_data[1]),
               latitude=lat_lon_parser.parse(p1_data[2]),
               longitude=lat_lon_parser.parse(p1_data[3]),
               px=int(p1_data[4]),
               py=int(p1_data[5]))
    p2 = Coordinates(x=float(p2_data[0]),
               y=float(p2_data[1]),
               latitude=lat_lon_parser.parse(p2_data[2]),
               longitude=lat_lon_parser.parse(p2_data[3]),
               px=int(p2_data[4]),
               py=int(p2_data[5]))
    return p1, p2


def validation(file_name: str):
    p1, p2 = get_reference_data(file_name)
    d_cartesian = cartesian_distance(p1, p2)
    d_gps = gps_distance(p1, p2)
    print("Error:", abs(d_cartesian - d_gps), "m")


if __name__ == '__main__':
    validation("config/reference_points.txt")
