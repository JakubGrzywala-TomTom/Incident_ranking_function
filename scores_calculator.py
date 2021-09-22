from converters import list_from_string

from math import degrees, atan2, sin, cos, radians
from datetime import datetime

from geopy.distance import geodesic
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points


# TRUE -> filter out the message, FALSE -> leave it
def filter_out_function(distance_between_points: float,
                        inner_radius: int,
                        outer_radius: int,
                        frc: str,
                        event: str,
                        categories: dict,
                        file_creation_dt: datetime,
                        incident_starttime_dt: datetime,
                        bearing_filter: bool) -> bool:

    # instantiating those in "incident_ranking_function" would be much more efficient
    inn_r_frc_list = list_from_string(str(categories["inn_r"]))
    out_r_frc_list = list_from_string(str(categories["out_r"]))
    third_r_frc_list = list_from_string(str(categories["3rd_r_frcs"]))
    third_r_event_list = list_from_string(str(categories["3rd_r_events"]))
    excluded_completely = list_from_string(str(categories["excluded_completely"]))

    # One colossal, enormous, gigantic if XD
    if (
        (event in excluded_completely)
        or bearing_filter
        or (file_creation_dt < incident_starttime_dt)
        or ((distance_between_points <= inner_radius) and (frc in inn_r_frc_list))
        or ((distance_between_points > inner_radius) and (distance_between_points <= outer_radius) and (frc in out_r_frc_list))
        or ((distance_between_points > outer_radius) and not ((frc in third_r_frc_list) and (event in third_r_event_list)))
    ):
        return True
    else:
        return False


def prepare_bearing_filter_values(ccp_dest_bearing: float,
                                  plus_minus_range: int) -> tuple:
    ccp_dest_bearing_left = ccp_dest_bearing - plus_minus_range
    if ccp_dest_bearing_left < 0:
        ccp_dest_bearing_left = 360 - abs(ccp_dest_bearing_left)

    ccp_dest_bearing_right = ccp_dest_bearing + plus_minus_range
    if ccp_dest_bearing_right > 360:
        ccp_dest_bearing_right = ccp_dest_bearing_right - 360

    return ccp_dest_bearing_left, ccp_dest_bearing_right


# TRUE -> filter out the message, FALSE -> leave it
def filter_out_bearing(ccp_dest_bearing: float,
                       ccp_incident_bearing: float,
                       bearing_filter_range: int,
                       bearing_filter_boundaries: tuple,
                       ccp_incident_distance: float,
                       inner_radius: int) -> bool:
    if ccp_incident_distance > inner_radius:
        if ccp_dest_bearing >= (360 - abs(bearing_filter_range)) or ccp_dest_bearing <= abs(bearing_filter_range):
            if ccp_incident_bearing >= bearing_filter_boundaries[0] or ccp_incident_bearing <= bearing_filter_boundaries[1]:
                return False
            else:
                return True
        else:
            if bearing_filter_boundaries[0] <= ccp_incident_bearing <= bearing_filter_boundaries[1]:
                return False
            else:
                return True
    else:
        return False


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


# set of 5 main functions calculating each score
def calc_distance_score(distance_between_points: float,
                        outer_radius: int) -> float:
    if distance_between_points != float(-100):
        distance_score_value = 1 - (distance_between_points/outer_radius)
        return round(distance_score_value, 5)
    else:
        return float(-100)


def calc_event_score(incident_type: str,
                     categories: dict) -> float:
    if incident_type != "Error":
        # watch out for event_score == 0, that means
        # we do not have certain event type covered in input.json
        event_score = 0
        for event_key, event_value in categories.items():
            if incident_type == event_key:
                event_score = event_value
                break
            else:
                continue
        return event_score
    else:
        return float(-100)


def calc_frc_score(incident_frc: str,
                   categories: dict) -> float:
    if incident_frc != "Error":
        frc_score = 0
        for frc_key, frc_value in categories.items():
            if incident_frc == frc_key:
                frc_score = frc_value
                break
            else:
                continue
        return frc_score
    else:
        return float(-100)


def calc_delay_score(delay: int,
                     categories: dict) -> float:
    if delay != -100:
        delay_score = 1
        for k, v in categories.items():
            if int(delay) < int(k):
                delay_score = v
                break
            else:
                continue
        return float(delay_score)
    else:
        return 0


def calc_radius_boost_score(distance_between_points: float,
                            inner_radius: float,
                            categories: dict) -> float:
    if distance_between_points != float(-100):
        close_radius_boost = int(list(categories.keys())[0])
        if distance_between_points < close_radius_boost:
            return float(categories["4"])
        elif close_radius_boost < distance_between_points < inner_radius:
            return float(categories["inn_r"])
        else:
            return float(categories["else"])
    else:
        return float(-100)


# final incident ranking function
def calc_rank(weights: dict,
              filter_out: bool,
              distance_score: float,
              event_score: float,
              frc_score: float,
              delay_score: float,
              radius_boost_score: float) -> float:

    if (filter_out is False) and (distance_score != -100) and (event_score != -100) \
       and (frc_score != -100) and (delay_score != -100) and (radius_boost_score != -100):

        incident_ranking_score = (weights["distance_score"] * distance_score
                                  + weights["event_score"] * event_score
                                  + weights["frc_score"] * frc_score
                                  + weights["delay_score"] * delay_score
                                  + weights["radius_boost_score"] * radius_boost_score)
        return incident_ranking_score
    else:
        return float(-100)
