import xml.etree.ElementTree as Et


useful_namespaces = {
    "main": "http://www.tomtom.com/service/ttix",                             # 0
    "messageManagement": "http://www.tomtom.com/service/common/msgm",         # 1
    "openLR": "http://www.openlr.org/openlr",                                 # 2
    "locationDescription": "http://www.tomtom.com/service/common/LocDescr",   # 3
    "eventDescription": "http://www.tomtom.com/service/common/EventAdt",      # 4
    "effectInfo": "http://www.tomtom.com/service/common/effect",              # 5
    "tmc": "http://www.tomtom.com/service/common/TmcEv",                      # 6
}


def register_all_namespaces(file):
    """
    Function extract namespaces from given file and assigns to dict.
    Configuration of keys and values differs (country or time differences, no idea).
    Anyway, <messageManagement> value:
    "http://www.tomtom.com/service/common/msgm" can once be ns2:, in other case ns7:, and so on...

    Next function (order_relevant_namespaces) filters only needed namespaces and orders keys in desirable order.
    """
    namespaces = dict([node for _, node in Et.iterparse(file, events=["start-ns"])])
    for ns in namespaces:
        """
        to get register_namespace to work two lines in original xml.etree.ElementTree lib had to be commented out
        1006 and 1007 in python 3.9.2 version: they were responsible for blocking registration of "ns*" namespaces
        and were raising an ValueError("Prefix format reserved for internal use")
        """
        Et.register_namespace(ns, namespaces[ns])
    return namespaces


def order_relevant_namespaces(current_ns_keys: tuple,
                              current_ns_vals: tuple) -> list:
    """
    Xml tags always have the same namespace values, but under changing tags
    Sometimes <messageManagement> is under "ns:7", sometimes under "ns:11".
    But the value of namespace is always "http://www.tomtom.com/service/common/msgm".

    Function reorders currently used ns keys into order of known, useful ns values (one from "useful_namespaces" var).
    So it can be easily used in parsing xml.
    """
    relevant_ns_order = []

    for val in useful_namespaces.values():
        if val in current_ns_vals:
            relevant_ns_key = current_ns_keys[current_ns_vals.index(val)]
            if relevant_ns_key == "":
                relevant_ns_order.append(relevant_ns_key)
            else:
                relevant_ns_order.append(relevant_ns_key + ":")

    return relevant_ns_order


def get_incident_key(traffic_message: Et.Element,
                     namespaces: dict,
                     ns_mes_mng: str) -> str:
    try:
        message_management = traffic_message.find(f"{ns_mes_mng}messageManagement", namespaces)
        incident_key = message_management.find(f"{ns_mes_mng}key", namespaces)
        return incident_key.text
    except AttributeError:
        return "Error"


def get_incident_pos(traffic_message: Et.Element,
                     namespaces: dict,
                     ns_main: str,
                     ns_olr: str,
                     ns_loc_desc: str) -> tuple:
    location = traffic_message.find(f"{ns_main}location", namespaces)
    try:
        return get_incident_location_from_bbox(location, namespaces, ns_main)
    except AttributeError:
        try:
            return get_incident_location_from_location_description(location, namespaces, ns_loc_desc)
        except AttributeError:
            try:
                return get_incident_location_from_openlr(location, namespaces, ns_olr)
            except AttributeError:
                return "Error", "Error"


def get_incident_location_from_openlr(location: Et.Element,
                                      namespaces: dict,
                                      ns_olr: str) -> tuple:
    open_lr = location.find(f"{ns_olr}OpenLR", namespaces)
    xml_location_reference = open_lr.find(f"{ns_olr}XMLLocationReference", namespaces)
    try:
        line_location_reference = xml_location_reference.find(f"{ns_olr}LineLocationReference", namespaces)
        location_reference_point = line_location_reference.find(f"{ns_olr}LocationReferencePoint", namespaces)
        coordinates = location_reference_point.find(f"{ns_olr}Coordinates", namespaces)
    except AttributeError:
        point_location_reference = xml_location_reference.find(f"{ns_olr}PointLocationReference", namespaces)
        point_along_line = point_location_reference.find(f"{ns_olr}PointAlongLine", namespaces)
        location_reference_point = point_along_line.find(f"{ns_olr}LocationReferencePoint", namespaces)
        coordinates = location_reference_point.find(f"{ns_olr}Coordinates", namespaces)
    latitude = coordinates.find(f"{ns_olr}Latitude", namespaces)
    longitude = coordinates.find(f"{ns_olr}Longitude", namespaces)
    return float(latitude.text), float(longitude.text)


def get_incident_location_from_location_description(location: Et.Element,
                                                    namespaces: dict,
                                                    ns_loc_desc: str) -> tuple:
    location_description = location.find(f"{ns_loc_desc}locationDescription", namespaces)
    start_location = location_description.find(f"{ns_loc_desc}startLocation", namespaces)
    latitude = start_location.find(f"{ns_loc_desc}Latitude", namespaces)
    longitude = start_location.find(f"{ns_loc_desc}Longitude", namespaces)
    return float(latitude.text), float(longitude.text)


def get_incident_location_from_bbox(location: Et.Element,
                                    namespaces: dict,
                                    ns_main: str) -> tuple:
    location_general = location.find(f"{ns_main}locationGeneral", namespaces)
    bbox = location_general.find(f"{ns_main}boundingBox", namespaces)
    lower_left = bbox.find(f"{ns_main}LowerLeft", namespaces)
    ll_latitude = lower_left.find(f"{ns_main}Latitude", namespaces)
    ll_longitude = lower_left.find(f"{ns_main}Longitude", namespaces)

    upper_right = bbox.find(f"{ns_main}UpperRight", namespaces)
    ur_latitude = upper_right.find(f"{ns_main}Latitude", namespaces)
    ur_longitude = upper_right.find(f"{ns_main}Longitude", namespaces)
    return (float(ll_latitude.text), float(ll_longitude.text)), (float(ur_latitude.text), float(ur_longitude.text))


def get_incident_event(traffic_message: Et.Element,
                       namespaces: dict,
                       ns_mes_mng: str) -> str:
    try:
        message_management = traffic_message.find(f"{ns_mes_mng}messageManagement", namespaces)
        content_type = message_management.find(f"{ns_mes_mng}contentType", namespaces)
        return content_type.text
    except AttributeError:
        return "Error"


def get_jam_priority(traffic_message: Et.Element,
                     namespaces: dict,
                     ns_main: str,
                     ns_event_desc: str) -> str:
    try:
        event = traffic_message.find(f"{ns_main}event", namespaces)
        event_description = event.find(f"{ns_event_desc}eventDescription", namespaces)
        alert_c_codes = event_description.find(f"{ns_event_desc}alertCCodes", namespaces)
        eventCode = alert_c_codes.find(f"{ns_event_desc}eventCode", namespaces)
        return eventCode.text
    except AttributeError:
        return "Error"


def get_incident_frc(traffic_message: Et.Element,
                     namespaces: dict,
                     ns_main: str) -> str:
    try:
        location = traffic_message.find(f"{ns_main}location", namespaces)
        location_general = location.find(f"{ns_main}locationGeneral", namespaces)
        functional_road_class = location_general.find(f"{ns_main}functionalRoadClass", namespaces)
        return functional_road_class.text
    except AttributeError:
        return "Error"


def get_incident_delay(traffic_message: Et.Element,
                       namespaces: dict,
                       ns_main: str,
                       ns_effect_info: str) -> int:
    try:
        event = traffic_message.find(f"{ns_main}event", namespaces)
        effect_info = event.find(f"{ns_effect_info}effectInfo", namespaces)
        absolute_delay_seconds = effect_info.find(f"{ns_effect_info}absoluteDelaySeconds", namespaces)
        return int(absolute_delay_seconds.text)
    # most probably means this incident does not have any delay (e.g. all CLOSURES)
    except AttributeError:
        return -100


def get_incident_expiry(traffic_message: Et.Element,
                        namespaces: dict,
                        ns_mes_mng: str) -> float:
    try:
        message_management = traffic_message.find(f"{ns_mes_mng}messageManagement", namespaces)
        expires_minutes = message_management.find(f"{ns_mes_mng}expiresIn", namespaces)
        expires_days = int(expires_minutes.text) / 60 / 24
        return round(expires_days, 5)
    except AttributeError:
        return -100


def get_incident_starttime(traffic_message: Et.Element,
                           namespaces: dict,
                           ns_main: str,
                           ns_tmc: str) -> str:
    try:
        event = traffic_message.find(f"{ns_main}event", namespaces)
        tmc_event = event.find(f"{ns_tmc}tmcEvent", namespaces)
        start_time_utc = tmc_event.find(f"{ns_tmc}startTimeUTC", namespaces)
        return start_time_utc.text
    except AttributeError:
        return "Error"


def get_file_creationtime(meta_data: Et.Element,
                          namespaces: dict,
                          ns_main: str) -> str:
    try:
        creation_time_UTC = meta_data.find(f"{ns_main}creationTimeUTC", namespaces)
        return creation_time_UTC.text
    except AttributeError:
        return "Error"
