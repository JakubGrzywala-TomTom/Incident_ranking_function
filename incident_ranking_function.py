from xml_parser import (register_all_namespaces, get_incident_key, get_incident_pos,
                        get_incident_event, get_incident_frc, get_incident_delay,
                        get_incident_expiry, get_incident_starttime, get_file_creationtime,
                        order_relevant_namespaces)
from scores_calculator import (distance_between, calc_rank, ccp_string_to_tuple,
                               filter_out_function, calc_distance_score, calc_event_score,
                               calc_frc_score, calc_delay_score, calc_radius_boost_score)
from converter import string_to_datetime

from json import load
from os.path import join, dirname, abspath, exists, sep
from os import mkdir
from time import perf_counter
import sys
import xml.etree.ElementTree as Et

import pandas as pd
import numpy as np


def main():
    start_time = perf_counter()

    # ask for folder with input .json and input TTI .xml  in terminal after -f flag
    # or through sysin if script run from PyCharm configuration
    opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]

    if "-f" not in opts:
        folder_flag_value = input("Please, specify folder in output with input TTI .xml and .json configuration: "
                                  "(or write \"exit\" if you want to leave) ")
        if folder_flag_value == "exit":
            exit()
    else:
        folder_flag_value = args[opts.index("-f")]

    # check if folders for output exist, if not create it
    output_directory = join(dirname(abspath(__file__)), "output")
    if not exists(output_directory):
        mkdir(output_directory)
        print(output_directory + " had to be created.")

    dev_test_directory = join(dirname(abspath(__file__)), "output", "_dev_tests")
    if not exists(dev_test_directory):
        mkdir(dev_test_directory)
        print(dev_test_directory + " had to be created. Please, before rerun insert one TTI .xml and "
                                   "one config input.json file into it or folder next to it with name of your choice. "
                                   "Then specify folder name with '-f' flag during rerun.")
        exit()

    # set which folder contains input and will accept output files
    output_folder_rel_path = folder_flag_value.split(sep)
    if len(output_folder_rel_path) == 2 and output_folder_rel_path[0] == "output" and output_folder_rel_path[1] != "":
        output_work_directory = join(dirname(abspath(__file__)), output_folder_rel_path[0], output_folder_rel_path[1])
    elif len(output_folder_rel_path) == 1:
        output_work_directory = join(dirname(abspath(__file__)), "output", output_folder_rel_path[0])
    else:
        output_work_directory = "lipppa"
        print("PLease, specify existing folder within 'output' folder. "
              "\nEither by writing folder name by itself after '-f' or '-f output\\<folder-name>'")
        exit()

    # load json file with current car position, radii and incident ranking method's category scores
    try:
        config_json_file = join(output_work_directory, "input.json")
        with open(config_json_file) as input_json:
            input_info = load(input_json)
    except FileNotFoundError:
        print("PLease, specify existing folder within 'output' folder. "
              "\nEither by writing folder name by itself after '-f' or '-f output\\<folder-name>'")
        exit()

    # load TTI XML file
    try:
        xml_file = str(input_info["XML_file"])
        if str(xml_file).endswith(".xml"):
            tree = Et.parse(join(output_work_directory, xml_file))
            namespaces = register_all_namespaces(join(output_work_directory, xml_file))
        else:
            tree = Et.parse(join(output_work_directory, xml_file + ".xml"))
            namespaces = register_all_namespaces(join(output_work_directory, xml_file + ".xml"))
        root = tree.getroot()
    except FileNotFoundError:
        print(f"TTI .xml file specified in input.json was not found in this folder: {output_work_directory}."
              f"\nMight be that you there's a typo in XML_file object in input.json.")
        exit()

    # create namespaces lists to dynamically assign keys to xml parsing functions
    ns_keys = tuple(namespaces.keys())
    ns_vals = tuple(namespaces.values())
    relevant_ns_order = order_relevant_namespaces(ns_keys, ns_vals)

    # assign trafficMessages to variable
    # no matter what is the "nsX:" of traffic message, on relevant_ns_order it will always be index 0
    meta_data = root.find(f"{relevant_ns_order[0]}metaData", namespaces)
    file_creation_dt = string_to_datetime(get_file_creationtime(meta_data, namespaces, relevant_ns_order[0]))
    traffic_messages = root.findall(f"{relevant_ns_order[0]}trafficMessage", namespaces)
    traffic_messages_number = len(traffic_messages)

    # create pandas dataframe for collecting scores and sorting/limiting output file
    dataframe = pd.DataFrame(columns=["incident_key", "filter_out",
                                      "expiry(days)", "start_time_utc",
                                      "distance", "distance_score", "radius_boost_score",
                                      "event", "event_score",
                                      "frc", "frc_score",
                                      "delay", "delay_score",
                                      "ranking_score"])

    # create tuple of lat and lon from coordinates string
    current_pos = ccp_string_to_tuple(input_info["ccp"])

    for number, traffic_message in enumerate(traffic_messages):
        # collect data from xml for certain message
        dataframe.at[number, "incident_key"] = get_incident_key(traffic_message, namespaces, relevant_ns_order[1])
        distance = distance_between(current_pos, get_incident_pos(traffic_message,
                                                                  namespaces,
                                                                  relevant_ns_order[0],
                                                                  relevant_ns_order[2],
                                                                  relevant_ns_order[3]))
        dataframe.at[number, "distance"] = distance
        incident_event = get_incident_event(traffic_message, namespaces, relevant_ns_order[1])
        dataframe.at[number, "event"] = incident_event
        incident_frc = get_incident_frc(traffic_message, namespaces, relevant_ns_order[0])
        dataframe.at[number, "frc"] = incident_frc
        if incident_event in input_info["excluded_from_delay_score"]:
            incident_delay = None
            dataframe.at[number, "delay"] = np.nan
        else:
            incident_delay = get_incident_delay(traffic_message,
                                                namespaces,
                                                relevant_ns_order[0],
                                                relevant_ns_order[5])
            dataframe.at[number, "delay"] = incident_delay
        incident_expiry = get_incident_expiry(traffic_message, namespaces, relevant_ns_order[1])
        dataframe.at[number, "expiry(days)"] = incident_expiry
        incident_starttime_str = get_incident_starttime(traffic_message,
                                                        namespaces,
                                                        relevant_ns_order[0],
                                                        relevant_ns_order[6])
        dataframe.at[number, "start_time_utc"] = incident_starttime_str
        incident_starttime_dt = string_to_datetime(incident_starttime_str)

        # first messages filtering based on distance and FRC/event type
        filter_out = filter_out_function(distance,
                                         input_info["inner_radius"],
                                         input_info["outer_radius"],
                                         incident_frc,
                                         incident_event,
                                         input_info["filtering_function"],
                                         file_creation_dt,
                                         incident_starttime_dt)
        dataframe.at[number, "filter_out"] = filter_out

        # calculate and collect scores
        distance_score = calc_distance_score(distance, input_info["outer_radius"])
        dataframe.at[number, "distance_score"] = distance_score
        radius_boost_score = calc_radius_boost_score(distance,
                                                     input_info["inner_radius"],
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
        ranking_score = calc_rank(input_info["weights"],
                                  filter_out,
                                  distance_score,
                                  event_score,
                                  frc_score,
                                  delay_score,
                                  radius_boost_score)
        dataframe.at[number, "ranking_score"] = ranking_score

        print("\rCalculated scores: " + str(number + 1) + " / " + str(traffic_messages_number), end='', flush=True)

    # save unsorted incidents with scores in the csv
    if xml_file.endswith(".xml"):
        xml_file = xml_file[:-4]
    dataframe.to_csv(join(output_work_directory, xml_file + "_all_scores.csv"), encoding='utf-8')

    # omit all excluded messages
    dataframe = dataframe[dataframe["ranking_score"] != -100]

    # sort, limit incidents and save in another csv
    dataframe_sorted = dataframe.sort_values(by="ranking_score", ascending=False)
    dataframe_sorted = dataframe_sorted.head(input_info["limit"])
    dataframe_sorted.to_csv(join(output_work_directory, xml_file + "_limited_scores.csv"), encoding='utf-8')

    # go through trafficMessages from original xml again
    # and compare incident keys in there to list of keys after scoring, sorting and limiting
    comparison_list = dataframe_sorted["incident_key"].tolist()
    for traffic_message in root.findall(f"{relevant_ns_order[0]}trafficMessage", namespaces):
        incident_key = get_incident_key(traffic_message, namespaces, relevant_ns_order[1])
        if incident_key in comparison_list:
            continue
        else:
            root.remove(traffic_message)

    tree = Et.ElementTree(root)
    tree.write(join(output_work_directory, xml_file + "_OUTPUT.xml"),
               encoding='utf-8',
               xml_declaration=True,
               default_namespace=None)

    end_time = perf_counter()
    print(f"\nScript finished in: {end_time - start_time} seconds")
    print("\nNumber of incidents in output .xml: " + str(dataframe_sorted["incident_key"].count()) +
          "\nLimit was: " + str(input_info["limit"]))


if __name__ == "__main__":
    main()
