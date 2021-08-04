from xml_parser import (register_all_namespaces, get_incident_key, get_incident_pos,
                        get_incident_event, get_incident_frc, get_incident_delay)
from scores_calculator import (distance_between, calc_rank,
                               calc_distance_score, calc_event_score, calc_horizon_score,
                               calc_frc_score, calc_delay_score, calc_radius_boost_score)

from json import load
from os.path import join, dirname, abspath, exists
from os import mkdir
import xml.etree.ElementTree as Et

import pandas as pd
import numpy as np

def ccp_string_to_tuple(ccp: str) -> tuple:
    lat = float(ccp.split(',')[0].strip())
    lon = float(ccp.split(',')[1].strip())
    return lat, lon


if __name__ == "__main__":
    # load json file with current car position, radii and incident ranking method's category scores
    with open("input.json") as input_json:
        input_info = load(input_json)

    # check if folders for input xmls and output files exist, if not create them
    xml_files_directory = join(dirname(abspath(__file__)), "TTI_XMLs")
    if not exists(xml_files_directory):
        mkdir(xml_files_directory)
    output_files_directory = join(dirname(abspath(__file__)), "OUTPUT")
    if not exists(output_files_directory):
        mkdir(output_files_directory)

    # load TTI XML file
    xml_file = input_info["XML_file"]
    tree = Et.parse(join(xml_files_directory, xml_file + ".xml"))
    namespaces = register_all_namespaces(join(xml_files_directory, xml_file + ".xml"))
    root = tree.getroot()

    #  compare read namespaces to original ones?
    #  I noticed they can change in time comparing to some files from year ago
    #  so maybe this change can be caught here

    # create pandas dataframe for collecting scores and sorting/limiting output file
    dataframe = pd.DataFrame(columns=["incident_key",
                                      "distance", "distance_score", "horizon_score", "radius_boost_score",
                                      "event", "event_score",
                                      "frc", "frc_score",
                                      "delay", "delay_score",
                                      "ranking_score"])

    # create tuple of lat and lon from coordinates string
    current_pos = ccp_string_to_tuple(input_info["ccp"])

    for number, traffic_message in enumerate(root.findall('trafficMessage', namespaces)):
        dataframe.at[number, "incident_key"] = get_incident_key(traffic_message, namespaces)

        distance = distance_between(current_pos, get_incident_pos(traffic_message, namespaces))
        dataframe.at[number, "distance"] = distance

        # bearing = bearing_between(current_pos, incident_pos)
        # print(incident_key + ":     " + str(incident_pos) + "=>" + str(bearing))

        distance_score = calc_distance_score(distance, input_info["outer_radius"])
        dataframe.at[number, "distance_score"] = distance_score

        horizon_score = calc_horizon_score(distance, input_info["inner_radius"], input_info["outer_radius"])
        dataframe.at[number, "horizon_score"] = horizon_score

        radius_boost_score = calc_radius_boost_score(distance,
                                                     input_info["inner_radius"],
                                                     input_info["radius_boost_score"])
        dataframe.at[number, "radius_boost_score"] = radius_boost_score

        incident_event = get_incident_event(traffic_message, namespaces)
        dataframe.at[number, "event"] = incident_event
        event_score = calc_event_score(incident_event, input_info["event_score"])
        dataframe.at[number, "event_score"] = event_score

        incident_frc = get_incident_frc(traffic_message, namespaces)
        dataframe.at[number, "frc"] = incident_frc
        frc_score = calc_frc_score(incident_frc, input_info["frc_score"])
        dataframe.at[number, "frc_score"] = frc_score

        # TODO: some incidents do not have delays so they should not receive delay score
        #  eg. CLOSURES should get delay score 1 (max value)?
        if incident_event not in input_info["excluded_from_delay_score"]:
            incident_delay = get_incident_delay(traffic_message,
                                                namespaces)
            dataframe.at[number, "delay"] = incident_delay
            delay_score = calc_delay_score(incident_delay, input_info["delay_score"])
            dataframe.at[number, "delay_score"] = delay_score
        else:
            delay_score = 1
            dataframe.at[number, "delay"] = np.nan
            dataframe.at[number, "delay_score"] = delay_score

        ranking_score = calc_rank(input_info["weights"], distance_score, event_score,
                                  horizon_score, frc_score, delay_score, radius_boost_score)
        dataframe.at[number, "ranking_score"] = ranking_score

    # save unsorted incidents with scores in the csv
    dataframe.to_csv(join("OUTPUT", xml_file + "_all_ranking_scores.csv"), encoding='utf-8')

    # omit -1 ranking scores (outside of radii)
    dataframe = dataframe[dataframe["ranking_score"] != -1]

    # sort, limit incidents and save in another csv
    dataframe_sorted = dataframe.sort_values(by="ranking_score", ascending=False)
    dataframe_sorted = dataframe_sorted.head(input_info["limit"])
    dataframe_sorted.to_csv(join("OUTPUT", xml_file + "_ranked_limited_scores.csv"), encoding='utf-8')

    # go through trafficMessages from original xml again
    # and compare incident keys in there to list of keys after scoring, sorting and limiting
    comparison_list = dataframe_sorted["incident_key"].tolist()
    for traffic_message in root.findall('trafficMessage', namespaces):
        incident_key = get_incident_key(traffic_message, namespaces)
        if incident_key in comparison_list:
            continue
        else:
            root.remove(traffic_message)

    tree = Et.ElementTree(root)
    tree.write(join("OUTPUT", xml_file + "_ranked_limited.xml"),
               encoding='utf-8',
               xml_declaration=True,
               default_namespace=None)
