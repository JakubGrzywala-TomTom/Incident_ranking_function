# SET OF 6 SCORES CALCULATING FUNCTIONS
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
            return float(categories[f"{close_radius_boost}"])
        elif close_radius_boost < distance_between_points < inner_radius:
            return float(categories["inn_r"])
        else:
            return float(categories["else"])
    else:
        return float(-100)


def calc_ccp_dest_line_distance_score(distance_between_points: float,
                                      buffer: float) -> float:
    if distance_between_points != float(-100):
        distance_score_value = 1 - (distance_between_points / buffer)
        return round(distance_score_value, 5)
    else:
        return float(-100)


# FINAL INCIDENT RANKING FUNCTION
def calc_rank(weights: dict,
              filter_out: bool,
              distance_score: float,
              event_score: float,
              frc_score: float,
              delay_score: float,
              radius_boost_score: float,
              ccp_dest_line_distance_score: float) -> float:

    if (filter_out is False) and (distance_score != -100) and (event_score != -100) and (frc_score != -100) \
       and (delay_score != -100) and (radius_boost_score != -100) and (ccp_dest_line_distance_score != -100):

        incident_ranking_score = (weights["distance_score"] * distance_score
                                  + weights["event_score"] * event_score
                                  + weights["frc_score"] * frc_score
                                  + weights["delay_score"] * delay_score
                                  + weights["radius_boost_score"] * radius_boost_score
                                  + weights["ccp_dest_line_score"] * ccp_dest_line_distance_score)
        return incident_ranking_score
    else:
        return float(-100)
