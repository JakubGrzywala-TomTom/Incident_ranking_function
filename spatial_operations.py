from math import degrees, atan2, sin, cos, radians

from geopy.distance import geodesic
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points


def distance_between(current_pos: tuple,
                     incident_pos: tuple) -> float:
    if isinstance(incident_pos[0], float):
        return geodesic(current_pos, incident_pos, ellipsoid="WGS-84").km
    elif incident_pos[0] == "Error":
        return float(-100)


# taken from https://www.igismap.com/formula-to-find-bearing-or-heading-angle-between-two-points-latitude-longitude/
def bearing_between(current_pos: tuple,
                    incident_pos: tuple) -> int:
    cur_lat = radians(current_pos[0])
    cur_lon = radians(current_pos[1])
    inc_lat = radians(incident_pos[0])
    inc_lon = radians(incident_pos[1])
    diff_lon = inc_lon - cur_lon
    y = cos(inc_lat) * sin(diff_lon)
    x = cos(cur_lat) * sin(inc_lat) - sin(cur_lat) * cos(inc_lat) * cos(diff_lon)
    # with "degrees(atan2(y, x))" values after 180 are with "-" and are in reverse (350 bearing is -10)
    # it needs conversion to full 360 values
    bearing = degrees(atan2(y, x))
    if bearing < 0:
        return int(360 + bearing)
    else:
        return int(bearing)


def create_ccp_destination_line(ccp: tuple,
                                destination: tuple) -> LineString:
    return LineString([(ccp[1], ccp[0]), (destination[1], destination[0])])


def find_nearest_line_part_to_incident(ccp_destination_line: LineString,
                                       incident_pos: tuple) -> Point:
    point = Point(incident_pos[1], incident_pos[0])
    return nearest_points(ccp_destination_line, point)[0]


def find_nearest_incident_end(current_pos: tuple,
                              incident_pos: tuple,) -> tuple:
    if not isinstance(incident_pos[0], tuple):
        return incident_pos
    else:
        lower_left_distance = geodesic(current_pos, incident_pos[0], ellipsoid="WGS-84").km
        upper_right_distance = geodesic(current_pos, incident_pos[1], ellipsoid="WGS-84").km
        if lower_left_distance < upper_right_distance:
            return incident_pos[0]
        else:
            return incident_pos[1]
