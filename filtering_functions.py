from datetime import datetime


# MAIN FILTERING FUNCTION
# TRUE -> filter out the message, FALSE -> leave it
def filter_out_function(distance_between_points: float,
                        inner_radius: int,
                        outer_radius: int,
                        third_radius: int,
                        frc: str,
                        event: str,
                        categories: dict,
                        file_creation_dt: datetime,
                        incident_starttime_dt: datetime,
                        bearing_filter: bool) -> bool:

    # First stage of filtering, cleaning messages outside of 3rd radius
    # -1 third radius means it will be "endless"
    if third_radius != -1 and third_radius < distance_between_points:
        return True

    # One colossal, enormous, gigantic if XD
    if (
        (event in categories["excluded_completely"])
        or bearing_filter
        or (file_creation_dt < incident_starttime_dt)
        or ((distance_between_points <= inner_radius) and (frc in categories["inn_r_frcs_exclude"]))
        or ((distance_between_points > inner_radius) and (distance_between_points <= outer_radius) and (frc in categories["out_r_frcs_exclude"]))
        or ((distance_between_points > outer_radius) and not ((frc in categories["3rd_r_frcs_include"]) and (event in categories["3rd_r_events_include"])))
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
    if plus_minus_range == 0:
        return 0, 0
    else:
        ccp_dest_bearing_left = ccp_dest_bearing - plus_minus_range
        if ccp_dest_bearing_left < 0:
            ccp_dest_bearing_left = 360 - abs(ccp_dest_bearing_left)

        ccp_dest_bearing_right = ccp_dest_bearing + plus_minus_range
        if ccp_dest_bearing_right > 360:
            ccp_dest_bearing_right = ccp_dest_bearing_right - 360

        return ccp_dest_bearing_left, ccp_dest_bearing_right
