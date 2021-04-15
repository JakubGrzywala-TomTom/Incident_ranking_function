import xml.etree.ElementTree as Et

"""
namespaces from first testfile
which was Birmingham_LUX_TTI_External_2021-03-25_27832d5d-a9b5-4abd-a8ae-e4d75d713c02.xml
when testing some older files from 2020-04 I noticed the order is different
"""
original_namespaces = {
    "": "http://www.tomtom.com/service/ttix",
    "ns2": "http://www.tomtom.com/service/common/TmcLR",
    "ns3": "http://www.tomtom.com/traffic/lasvegas/TTLR",
    "ns4": "http://www.openlr.org/openlr",
    "ns5": "http://www.tomtom.com/service/common/LocDescr",
    "ns6": "http://www.tomtom.com/service/common/lanes",
    "ns7": "http://www.tomtom.com/service/common/msgm",
    "ns8": "http://www.tomtom.com/service/common/TmcEv",
    "ns9": "http://www.tomtom.com/service/common/EventAdt",
    "ns10": "http://www.tomtom.com/service/common/effect",
    "ns11": "http://www.tomtom.com/service/common/jamtail",
    "ns12": "http://www.tomtom.com/service/common/src"
}


def register_all_namespaces(file):
    namespaces = dict([node for _, node in Et.iterparse(file, events=["start-ns"])])
    for ns in namespaces:
        """
        to get register_namespace to work two lines in original xml.etree.ElementTree lib had to be commented out
        1006 and 1007 in python 3.9.2 version: they were responsible for blocking registration of "ns*" namespaces
        and were raising an ValueError("Prefix format reserved for internal use")
        """
        Et.register_namespace(ns, namespaces[ns])
    return namespaces


def get_incident_key(traffic_message: Et.Element, namespaces: dict) -> str:
    message_management = traffic_message.find("ns7:messageManagement", namespaces)
    incident_key = message_management.find("ns7:key", namespaces)
    return incident_key.text


def get_incident_pos(traffic_message: Et.Element, namespaces: dict) -> tuple:
    location = traffic_message.find("location", namespaces)
    open_lr = location.find("ns4:OpenLR", namespaces)
    xml_location_reference = open_lr.find("ns4:XMLLocationReference", namespaces)
    try:
        line_location_reference = xml_location_reference.find("ns4:LineLocationReference", namespaces)
        location_reference_point = line_location_reference.find("ns4:LocationReferencePoint", namespaces)
        coordinates = location_reference_point.find("ns4:Coordinates", namespaces)
    except AttributeError:
        point_location_reference = xml_location_reference.find("ns4:PointLocationReference", namespaces)
        point_along_line = point_location_reference.find("ns4:PointAlongLine", namespaces)
        location_reference_point = point_along_line.find("ns4:LocationReferencePoint", namespaces)
        coordinates = location_reference_point.find("ns4:Coordinates", namespaces)
    latitude = coordinates.find("ns4:Latitude", namespaces)
    longitude = coordinates.find("ns4:Longitude", namespaces)
    incident_pos = (float(latitude.text), float(longitude.text))
    return incident_pos


def get_incident_event(traffic_message: Et.Element, namespaces: dict) -> str:
    message_management = traffic_message.find("ns7:messageManagement", namespaces)
    content_type = message_management.find("ns7:contentType", namespaces)
    return content_type.text


def get_incident_frc(traffic_message: Et.Element, namespaces: dict) -> str:
    location = traffic_message.find("location", namespaces)
    location_general = location.find("locationGeneral", namespaces)
    functional_road_class = location_general.find("functionalRoadClass", namespaces)
    return functional_road_class.text


def get_incident_delay(ord_number: int,
                       incident_key: str,
                       traffic_message: Et.Element,
                       namespaces: dict) -> int:
    event = traffic_message.find("event", namespaces)
    # TODO: some incident seem to not have any delay info
    #  not only delay, but also no ns10:effectInfo
    effect_info = event.find("ns10:effectInfo", namespaces)
    if effect_info is None:
        absolute_delay_seconds = 0
    else:
        absolute_delay_seconds = effect_info.find("ns10:absoluteDelaySeconds", namespaces)
        if absolute_delay_seconds is None:
            # print(str(ord_number) + ") " + incident_key + ":   " + "no delay")
            absolute_delay_seconds = 0
        else:
            absolute_delay_seconds = int(absolute_delay_seconds.text)
    return absolute_delay_seconds
