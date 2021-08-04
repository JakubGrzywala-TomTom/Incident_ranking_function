from math import degrees, atan2, sin, cos, radians

from geopy.distance import geodesic


def distance_between(current_pos: tuple,
                     incident_pos: tuple) -> float:
    if isinstance(incident_pos[0], float):
        return geodesic(current_pos, incident_pos, ellipsoid="WGS-84").km
    elif isinstance(incident_pos[0], tuple):
        # logic for deciding which bbox coordinates are closer
        lower_left_distance = geodesic(current_pos, incident_pos[0], ellipsoid="WGS-84").km
        upper_right_distance = geodesic(current_pos, incident_pos[1], ellipsoid="WGS-84").km
        if lower_left_distance < upper_right_distance:
            return lower_left_distance
        else:
            return upper_right_distance
    elif incident_pos[0] == "Error":
        return float(-100)


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


def calc_horizon_score(distance_between_points: float,
                       inner_radius: int,
                       outer_radius: int) -> float:
    # the idea in this score is to get rid of messages outside of outer radius
    # that's why the ifs are structured like below
    if distance_between_points != float(-100) and distance_between_points <= inner_radius:
        return float(1)
    elif distance_between_points != float(-100) and distance_between_points <= outer_radius:
        return float(0)
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
              distance_score: float,
              event_score: float,
              horizon_score: float,
              frc_score: float,
              delay_score: float,
              radius_boost_score: float) -> float:

    if (distance_score != -100) and (event_score != -100) and (horizon_score != -100)\
       and (frc_score != -100) and (delay_score != -100) and (radius_boost_score != -100):

        incident_ranking_score = (weights["distance_score"] * distance_score
                                  + weights["event_score"] * event_score
                                  + weights["horizon_score"] * horizon_score
                                  + weights["frc_score"] * frc_score
                                  + weights["delay_score"] * delay_score
                                  + weights["radius_boost_score"] * radius_boost_score)
        return incident_ranking_score
    else:
        return float(-100)
