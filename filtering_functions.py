from converters import list_from_string

from datetime import datetime


# MAIN FILTERING FUNCTION
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
    inn_r_frc_list = list_from_string(str(categories["inn_r_exclude"]))
    out_r_frc_list = list_from_string(str(categories["out_r_exclude"]))
    third_r_frc_list = list_from_string(str(categories["3rd_r_frcs_include"]))
    third_r_event_list = list_from_string(str(categories["3rd_r_events_include"]))
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


# BEARING FILTERING
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


def prepare_bearing_filter_values(ccp_dest_bearing: float,
                                  plus_minus_range: int) -> tuple:
    ccp_dest_bearing_left = ccp_dest_bearing - plus_minus_range
    if ccp_dest_bearing_left < 0:
        ccp_dest_bearing_left = 360 - abs(ccp_dest_bearing_left)

    ccp_dest_bearing_right = ccp_dest_bearing + plus_minus_range
    if ccp_dest_bearing_right > 360:
        ccp_dest_bearing_right = ccp_dest_bearing_right - 360

    return ccp_dest_bearing_left, ccp_dest_bearing_right
