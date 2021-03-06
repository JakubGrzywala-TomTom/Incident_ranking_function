from converters import string_to_datetime, coordinates_string_to_tuple, list_from_string
from plot_maker import create_histogram
from filtering_functions import prepare_bearing_filter_values, filter_out_bearing, filter_out_function
from scoring_functions import (calc_distance_score, calc_event_score, calc_frc_score,
                               calc_delay_score, calc_radius_boost_score, calc_ccp_dest_line_distance_score,
                               calc_rank)
from spatial_functions import (distance_between, bearing_between, create_ccp_destination_line,
                               find_nearest_line_part_to_incident, find_nearest_incident_end)
from xml_parser import (register_all_namespaces, get_incident_key, get_incident_pos,
                        get_incident_event, get_jam_priority, get_incident_frc, get_incident_delay,
                        get_incident_expiry, get_incident_starttime, get_file_creationtime,
                        order_relevant_namespaces)

from json import load
from os.path import join, dirname, abspath, exists, sep
from os import mkdir
from time import perf_counter
import sys
import xml.etree.ElementTree as Et

import numpy as np
import pandas as pd


def main():
    start_time = perf_counter()

    # -----------------------------------
    # PHASE 1: COLLECTING PREDEFINED INFO

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

    if "-m" in opts:
        mode_flag_value = args[opts.index("-m")].lower().strip()
        if mode_flag_value == "around":
            around_mode_on = True
            bearing_mode_on = False
            line_mode_on = False
        elif mode_flag_value == "bearing":
            around_mode_on = False
            bearing_mode_on = True
            line_mode_on = False
        elif mode_flag_value == "line":
            around_mode_on = False
            bearing_mode_on = False
            line_mode_on = True
        else:
            print("Please specify (by writing after '-m' mode flag) one of three possible script modes:"
                  "\n    'around': to simulate car sending request without destination"
                  "\n    'bearing': to simulate car sending request with destination and usage of bearing filter"
                  "\n    'line': to simulate car sending request with destination and usage of ccp -> destination "
                  "line score")
            exit()
    # IF mode flag not used, then script goes into most simple "around" mode, simulating car request without destination
    else:
        around_mode_on = True
        bearing_mode_on = False
        line_mode_on = False

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

    # load json file with current car position, radii and incident ranking method's category scores, etc.
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
    dataframe = pd.DataFrame(columns=["incident_key", "incident_nearest_end_position",
                                      "expiry(days)", "start_time_utc",
                                      "distance", "distance_score", "radius_boost_score",
                                      "event", "jam_priority", "event_score",
                                      "frc", "frc_score",
                                      "delay", "delay_score",
                                      "bearing", "bearing_filter_out",
                                      "distance_incident_to_line", "route_line_distance_score",
                                      "filter_out", "ranking_score"])

    # create tuple of lat, lon from coordinates string
    # plus other needed variables
    current_pos = coordinates_string_to_tuple(input_info["ccp"])
    ranking_score_capping = float(input_info["ranking_score_capping"])
    filtering_rules = {}
    for k, v in input_info["filtering_function"].items():
        filtering_rules[k] = list_from_string(str(v))

    if bearing_mode_on or line_mode_on:
        destination_pos = coordinates_string_to_tuple(input_info["destination"])
        ccp_destination_line = create_ccp_destination_line(current_pos, destination_pos)
        ccp_destination_bearing = bearing_between(current_pos, destination_pos)
        bearing_filter_range = int(input_info["bearing_filter_range"])
        bearing_filter_boundaries = prepare_bearing_filter_values(ccp_destination_bearing, bearing_filter_range)

    # -------------------------------------
    # PHASE 2: COLLECT INCIDENTS ATTRIBUTES

    for number, traffic_message in enumerate(traffic_messages):
        dataframe.at[number, "incident_key"] = get_incident_key(traffic_message, namespaces, relevant_ns_order[1])
        incident_expiry = get_incident_expiry(traffic_message, namespaces, relevant_ns_order[1])
        dataframe.at[number, "expiry(days)"] = incident_expiry
        incident_starttime_str = get_incident_starttime(traffic_message,
                                                        namespaces,
                                                        relevant_ns_order[0],
                                                        relevant_ns_order[6])
        dataframe.at[number, "start_time_utc"] = incident_starttime_str
        incident_starttime_dt = string_to_datetime(incident_starttime_str)
        nearest_incident_end = find_nearest_incident_end(current_pos, get_incident_pos(traffic_message,
                                                                                       namespaces,
                                                                                       relevant_ns_order[0],
                                                                                       relevant_ns_order[2],
                                                                                       relevant_ns_order[3]))
        dataframe.at[number, "incident_nearest_end_position"] = (str(nearest_incident_end[0])
                                                                 + ", "
                                                                 + str(nearest_incident_end[1]))
        distance_incident_to_ccp = distance_between(current_pos, nearest_incident_end)
        dataframe.at[number, "distance"] = distance_incident_to_ccp
        incident_event = get_incident_event(traffic_message, namespaces, relevant_ns_order[1])
        dataframe.at[number, "event"] = incident_event
        if incident_event.find("JAM") != -1:
            jam_priority = get_jam_priority(traffic_message, namespaces, relevant_ns_order[0], relevant_ns_order[4])
            dataframe.at[number, "jam_priority"] = jam_priority
        else:
            jam_priority = "Error"
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

        # ---------------------------
        # PHASE 3: SCORES CALCULATION

        distance_score = calc_distance_score(distance_incident_to_ccp, input_info["outer_radius"])
        dataframe.at[number, "distance_score"] = distance_score
        radius_boost_score = calc_radius_boost_score(distance_incident_to_ccp,
                                                     input_info["inner_radius"],
                                                     input_info["radius_boost_score"])
        dataframe.at[number, "radius_boost_score"] = radius_boost_score
        event_score = calc_event_score(incident_event,
                                       input_info["event_score"],
                                       jam_priority,
                                       input_info["jam_priority"])
        dataframe.at[number, "event_score"] = event_score
        frc_score = calc_frc_score(incident_frc, input_info["frc_score"])
        dataframe.at[number, "frc_score"] = frc_score
        if incident_delay is None:
            delay_score = 1
            dataframe.at[number, "delay_score"] = delay_score
        else:
            delay_score = calc_delay_score(incident_delay, input_info["delay_score"])
            dataframe.at[number, "delay_score"] = delay_score

        # Scenario 1: when car requests traffic without destination location, e.g. when starting engine and info system.
        # This scenario does not utilize any bearing filters or scores based on line between ccp and destination.
        # Just incidents around ccp scored by importance and filtered out properly.
        if around_mode_on:
            filter_out = filter_out_function(distance_incident_to_ccp,
                                             input_info["inner_radius"],
                                             input_info["outer_radius"],
                                             input_info["3rd_radius"],
                                             incident_frc,
                                             incident_event,
                                             filtering_rules,
                                             file_creation_dt,
                                             incident_starttime_dt,
                                             bearing_filter=False)
            dataframe.at[number, "filter_out"] = filter_out
            ranking_score = calc_rank(input_info["weights"],
                                      filter_out,
                                      distance_score,
                                      event_score,
                                      frc_score,
                                      delay_score,
                                      radius_boost_score,
                                      ccp_dest_line_distance_score=0)
            dataframe.at[number, "ranking_score"] = ranking_score

        # Scenarios when car requests for traffic with destination and route: two ways of calculating scores here
        else:
            # Scenario 2: using bearing filter, script will discard all messages outside of inner radius IF they are
            # not around ccp -> destination bearing (number of degrees left and right around this bearing)
            # Script creates some kind of "wedge" around ccp -> dest bearing.
            if bearing_mode_on:
                bearing = bearing_between(current_pos, nearest_incident_end)
                dataframe.at[number, "bearing"] = bearing
                bearing_filter = filter_out_bearing(ccp_destination_bearing,
                                                    bearing,
                                                    bearing_filter_range,
                                                    bearing_filter_boundaries,
                                                    distance_incident_to_ccp,
                                                    input_info["inner_radius"])
                dataframe.at[number, "bearing_filter_out"] = bearing_filter
                filter_out = filter_out_function(distance_incident_to_ccp,
                                                 input_info["inner_radius"],
                                                 input_info["outer_radius"],
                                                 input_info["3rd_radius"],
                                                 incident_frc,
                                                 incident_event,
                                                 filtering_rules,
                                                 file_creation_dt,
                                                 incident_starttime_dt,
                                                 bearing_filter)
                dataframe.at[number, "filter_out"] = filter_out
                ranking_score = calc_rank(input_info["weights"],
                                          filter_out,
                                          distance_score,
                                          event_score,
                                          frc_score,
                                          delay_score,
                                          radius_boost_score,
                                          ccp_dest_line_distance_score=0)
                dataframe.at[number, "ranking_score"] = ranking_score

            # Scenario 3: using score that orders incidents based on distance between them and ccp -> destination line.
            # Score will also eliminate all messages outside of "score buffer". IF messages limit is too low, script
            # will start from eliminating messages most remote from ccp -> dest line, event that they are inside buffer.
            elif line_mode_on:
                bearing = bearing_between(current_pos, nearest_incident_end)
                dataframe.at[number, "bearing"] = bearing
                bearing_filter = filter_out_bearing(ccp_destination_bearing,
                                                    bearing,
                                                    bearing_filter_range,
                                                    bearing_filter_boundaries,
                                                    distance_incident_to_ccp,
                                                    input_info["inner_radius"])
                dataframe.at[number, "bearing_filter_out"] = bearing_filter
                if not bearing_filter:
                    nearest_line_part_to_incident = find_nearest_line_part_to_incident(ccp_destination_line,
                                                                                       nearest_incident_end)
                    distance_incident_to_ccp_dest_line = distance_between((nearest_line_part_to_incident.y,
                                                                           nearest_line_part_to_incident.x),
                                                                          nearest_incident_end)
                    dataframe.at[number, "distance_incident_to_line"] = round(distance_incident_to_ccp_dest_line, 3)
                    ccp_dest_line_distance_score = calc_ccp_dest_line_distance_score(distance_incident_to_ccp_dest_line,
                                                                                     input_info["ccp_dest_buffer_[km]"])
                    dataframe.at[number, "route_line_distance_score"] = ccp_dest_line_distance_score
                else:
                    ccp_dest_line_distance_score = -100
                filter_out = filter_out_function(distance_incident_to_ccp,
                                                 input_info["inner_radius"],
                                                 input_info["outer_radius"],
                                                 input_info["3rd_radius"],
                                                 incident_frc,
                                                 incident_event,
                                                 filtering_rules,
                                                 file_creation_dt,
                                                 incident_starttime_dt,
                                                 bearing_filter)
                dataframe.at[number, "filter_out"] = filter_out
                ranking_score = calc_rank(input_info["weights"],
                                          filter_out,
                                          distance_score,
                                          event_score,
                                          frc_score,
                                          delay_score,
                                          radius_boost_score,
                                          ccp_dest_line_distance_score)
                dataframe.at[number, "ranking_score"] = ranking_score
            else:
                exit()

        print("\rCalculated scores: " + str(number + 1) + " / " + str(traffic_messages_number), end='', flush=True)

    # -------------------------------------------
    # PHASE 4: SAVE SCORESHEET AND FILTERED XML

    # save unsorted incidents with scores in the csv
    if xml_file.endswith(".xml"):
        xml_file = xml_file[:-4]
    dataframe.to_csv(join(output_work_directory, xml_file + "_all_scores.csv"), encoding='utf-8')

    # omit all excluded messages
    dataframe = dataframe[dataframe["ranking_score"] != -100]

    # sort and save histogram
    dataframe_sorted = dataframe.sort_values(by="ranking_score", ascending=False)
    create_histogram(dataframe_sorted["ranking_score"],
                     output_work_directory,
                     ranking_score_capping,
                     int(input_info["limit"]))

    # delete all rows below capping value
    dataframe_sorted = dataframe_sorted[dataframe_sorted["ranking_score"].astype(float) > ranking_score_capping]

    # limit incidents and save in another csv
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

    # ------------------------
    # PHASE X: PRINT OUT STATS

    end_time = perf_counter()
    print(
        f"\nScript finished in: {end_time - start_time} seconds"
        + f'\n\nCCP: {input_info["ccp"]}'
    )

    if bearing_mode_on or line_mode_on:
        print(
            f'Destination: {input_info["destination"]}'
            + f'\nCCP -> destination bearing: {ccp_destination_bearing}'
            + f'\nCCP -> destination distance [km]: {round(distance_between(current_pos, destination_pos), 3)}'
        )

    print(
        "\nNumber of incidents in output .xml: " + str(dataframe_sorted["incident_key"].count())
        + "\nLimit was: " + str(input_info["limit"])
        + "\nInner radius: " + str(input_info["inner_radius"])
        + "\nOuter radius: " + str(input_info["outer_radius"])
        + "\n3rd radius: " + str(input_info["3rd_radius"])
        + "\n\nOUTPUT XML STATISTICS:"
        + "\n\nDistance [km]: \n"
        + str(dataframe_sorted.agg({"distance": ["min", "max", "mean", "median"]}))
        + "\n\nEvents: \n" + str(dataframe_sorted["event"].value_counts())
        + "\n\nFRCs: \n" + str(dataframe_sorted["frc"].value_counts())
    )


if __name__ == "__main__":
    main()
