from xml_parser import (register_all_namespaces, get_incident_key, get_incident_pos,
                        get_incident_event, get_incident_frc, get_incident_delay)
from scores_calculator import (distance_between, calc_rank, ccp_string_to_tuple,
                               filter_out_function, calc_distance_score, calc_event_score,
                               calc_frc_score, calc_delay_score, calc_radius_boost_score)

from json import load
from os.path import join, dirname, abspath, exists
from os import mkdir
import sys
import xml.etree.ElementTree as Et

import pandas as pd
import numpy as np


def main():
    # ask for input .json filename in terminal after -f flag or through sysin if script run from PyCharm configuration
    opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]

    if "-f" not in opts:
        file = input("Please, specify input json file: "
                     "(or write \"exit\" if you want to leave) ")
        if file == "exit":
            exit()
    else:
        file = args[opts.index('-f')]

    # load json file with current car position, radii and incident ranking method's category scores
    with open(file) as input_json:
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
    if str(xml_file).endswith(".xml"):
        tree = Et.parse(join(xml_files_directory, xml_file))
        namespaces = register_all_namespaces(join(xml_files_directory, xml_file))
    else:
        tree = Et.parse(join(xml_files_directory, xml_file + ".xml"))
        namespaces = register_all_namespaces(join(xml_files_directory, xml_file + ".xml"))
    root = tree.getroot()
    traffic_messages = root.findall('trafficMessage', namespaces)
    traffic_messages_number = len(traffic_messages)

    # create pandas dataframe for collecting scores and sorting/limiting output file
    dataframe = pd.DataFrame(columns=["incident_key", "filter_out",
                                      "distance", "distance_score", "radius_boost_score",
                                      "event", "event_score",
                                      "frc", "frc_score",
                                      "delay", "delay_score",
                                      "ranking_score"])

    # create tuple of lat and lon from coordinates string
    current_pos = ccp_string_to_tuple(input_info["ccp"])

    for number, traffic_message in enumerate(traffic_messages):
        # collect data from xml for certain message
        dataframe.at[number, "incident_key"] = get_incident_key(traffic_message, namespaces)
        distance = distance_between(current_pos, get_incident_pos(traffic_message, namespaces))
        dataframe.at[number, "distance"] = distance
        incident_event = get_incident_event(traffic_message, namespaces)
        dataframe.at[number, "event"] = incident_event
        incident_frc = get_incident_frc(traffic_message, namespaces)
        dataframe.at[number, "frc"] = incident_frc
        if incident_event in input_info["excluded_from_delay_score"]:
            incident_delay = None
            dataframe.at[number, "delay"] = np.nan
        else:
            incident_delay = get_incident_delay(traffic_message, namespaces)
            dataframe.at[number, "delay"] = incident_delay

        # first messages filtering based on distance and FRC/event type
        filter_out = filter_out_function(distance, input_info["inner_radius"], input_info["outer_radius"],
                                         incident_frc, incident_event, input_info["filtering_function"])
        dataframe.at[number, "filter_out"] = filter_out

        # calculate and collect scores
        distance_score = calc_distance_score(distance, input_info["outer_radius"])
        dataframe.at[number, "distance_score"] = distance_score
        radius_boost_score = calc_radius_boost_score(distance, input_info["inner_radius"],
                                                     input_info["radius_boost_score"])
        dataframe.at[number, "radius_boost_score"] = radius_boost_score
        event_score = calc_event_score(incident_event, input_info["event_score"])
        dataframe.at[number, "event_score"] = event_score
        frc_score = calc_frc_score(incident_frc, input_info["frc_score"])
        dataframe.at[number, "frc_score"] = frc_score
        if incident_delay is None:
            delay_score = 1
            dataframe.at[number, "delay_score"] = delay_score
        else:
            delay_score = calc_delay_score(incident_delay, input_info["delay_score"])
            dataframe.at[number, "delay_score"] = delay_score

        # calculate and collect final score
        ranking_score = calc_rank(input_info["weights"], filter_out, distance_score,
                                  event_score, frc_score, delay_score, radius_boost_score)
        dataframe.at[number, "ranking_score"] = ranking_score

        print("\rCalculated scores: " + str(number + 1) + " / " + str(traffic_messages_number), end='', flush=True)

    # save unsorted incidents with scores in the csv
    dataframe.to_csv(join("OUTPUT", xml_file + "_all_scores.csv"), encoding='utf-8')

    # omit all excluded messages
    dataframe = dataframe[dataframe["ranking_score"] != -100]

    # sort, limit incidents and save in another csv
    dataframe_sorted = dataframe.sort_values(by="ranking_score", ascending=False)
    dataframe_sorted = dataframe_sorted.head(input_info["limit"])
    dataframe_sorted.to_csv(join("OUTPUT", xml_file + "_limited_scores.csv"), encoding='utf-8')

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
    tree.write(join("OUTPUT", xml_file + "_OUTPUT.xml"),
               encoding='utf-8',
               xml_declaration=True,
               default_namespace=None)


if __name__ == "__main__":
    main()