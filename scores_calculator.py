from math import degrees, atan2, sin, cos, radians

from geopy.distance import geodesic


def distance_between(current_pos: tuple,
                     incident_pos: tuple) -> float:
    return geodesic(current_pos, incident_pos, ellipsoid="WGS-84").km


# taken from https://www.igismap.com/formula-to-find-bearing-or-heading-angle-between-two-points-latitude-longitude/
def bearing_between(current_pos: tuple,
                    incident_pos: tuple) -> float:
    cur_lat = radians(current_pos[0])
    cur_lon = radians(current_pos[1])
    inc_lat = radians(incident_pos[0])
    inc_lon = radians(incident_pos[1])
    diff_lon = inc_lon - cur_lon
    y = cos(inc_lat) * sin(diff_lon)
    x = cos(cur_lat) * sin(inc_lat) - sin(cur_lat) * cos(inc_lat) * cos(diff_lon)
    return degrees(atan2(y, x))


# set of 6 main functions calculating each score
def calc_distance_score(distance_between_points: float,
                        outer_radius: int) -> float:
    distance_score_value = 1 - (distance_between_points/outer_radius)
    return round(distance_score_value, 5)


def calc_event_score(incident_type: str,
                     categories: dict) -> float:
    event_score = 0
    for event_key, event_value in categories.items():
        if incident_type == event_key:
            event_score = event_value
            break
        else:
            continue
    return event_score


def calc_horizon_score(distance_between_points: float,
                       inner_radius: int,
                       outer_radius: int) -> int:
    if distance_between_points <= inner_radius:
        horizon_score_value = 1
    elif distance_between_points <= outer_radius:
        horizon_score_value = 0
    else:
        # TODO: this None results in error when calculating score in "calc_rank" below
        #  TypeError: unsupported operand type(s) for *: 'float' and 'NoneType'
        horizon_score_value = None
    return horizon_score_value


def calc_frc_score(incident_frc: str,
                   categories: dict) -> float:
    frc_score = 0
    for frc_key, frc_value in categories.items():
        if incident_frc == frc_key:
            frc_score = frc_value
            break
        else:
            continue
    # TODO: setup logging for incidents that do not have frc???
    return frc_score


def calc_delay_score(delay: int,
                     categories: dict) -> float:
    delay_score = 1
    for k, v in categories.items():
        if int(delay) < int(k):
            delay_score = float(v)
            break
        else:
            continue
    return delay_score


def calc_radius_boost_score(distance_between_points: float,
                            inner_radius: float,
                            categories: dict) -> float:
    if distance_between_points < 4:
        radius_boost_score_value = categories["4"]
    elif 4 < distance_between_points < inner_radius:
        radius_boost_score_value = categories["inn_r"]
    else:
        radius_boost_score_value = categories["else"]
    return radius_boost_score_value


# final incident ranking function
def calc_rank(weights: dict,
              distance_score: float,
              event_score: float,
              horizon_score: float,
              frc_score: float,
              delay_score: float,
              radius_boost_score: float) -> float:
    incident_ranking_score = (weights["distance_score"] * distance_score
                              + weights["event_score"] * event_score
                              + weights["horizon_score"] * horizon_score
                              + weights["frc_score"] * frc_score
                              + weights["delay_score"] * delay_score
                              + weights["radius_boost_score"] * radius_boost_score)
    return incident_ranking_score
