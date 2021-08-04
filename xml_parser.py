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
    try:
        message_management = traffic_message.find("ns7:messageManagement", namespaces)
        incident_key = message_management.find("ns7:key", namespaces)
        return incident_key.text
    except AttributeError:
        return "Error"


def get_incident_pos(traffic_message: Et.Element, namespaces: dict) -> tuple:
    location = traffic_message.find("location", namespaces)
    try:
        return get_incident_location_from_openlr(location, namespaces)
    except AttributeError:
        try:
            return get_incident_location_from_location_description(location, namespaces)
        except AttributeError:
            try:
                return get_incident_location_from_bbox(location, namespaces)
            except AttributeError:
                return "Error", "Error"


def get_incident_location_from_openlr(location: Et.Element, namespaces: dict) -> tuple:
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
    return float(latitude.text), float(longitude.text)


def get_incident_location_from_location_description(location: Et.Element, namespaces: dict) -> tuple:
    location_description = location.find('ns5:locationDescription', namespaces)
    start_location = location_description.find('ns5:startLocation', namespaces)
    latitude = start_location.find('ns5:Latitude', namespaces)
    longitude = start_location.find('ns5:Longitude', namespaces)
    return float(latitude.text), float(longitude.text)


def get_incident_location_from_bbox(location: Et.Element, namespaces: dict) -> tuple:
    location_general = location.find('locationGeneral', namespaces)
    bbox = location_general.find('boundingBox', namespaces)
    lower_left = bbox.find('LowerLeft', namespaces)
    ll_latitude = lower_left.find('Latitude', namespaces)
    ll_longitude = lower_left.find('Longitude', namespaces)

    upper_right = bbox.find('UpperRight', namespaces)
    ur_latitude = upper_right.find('Latitude', namespaces)
    ur_longitude = upper_right.find('Longitude', namespaces)
    return (float(ll_latitude.text), float(ll_longitude.text)), (float(ur_latitude.text), float(ur_longitude.text))


def get_incident_event(traffic_message: Et.Element, namespaces: dict) -> str:
    try:
        message_management = traffic_message.find("ns7:messageManagement", namespaces)
        content_type = message_management.find("ns7:contentType", namespaces)
        return content_type.text
    except AttributeError:
        return "Error"


def get_incident_frc(traffic_message: Et.Element, namespaces: dict) -> str:
    # TODO: expand searching for frc to OpenLR > XMLLocationReference > LineAttributes > FRC
    try:
        location = traffic_message.find("location", namespaces)
        location_general = location.find("locationGeneral", namespaces)
        functional_road_class = location_general.find("functionalRoadClass", namespaces)
        return functional_road_class.text
    except AttributeError:
        return "Error"


def get_incident_delay(traffic_message: Et.Element, namespaces: dict) -> int:
    try:
        event = traffic_message.find("event", namespaces)
        effect_info = event.find("ns10:effectInfo", namespaces)
        absolute_delay_seconds = effect_info.find("ns10:absoluteDelaySeconds", namespaces)
        return int(absolute_delay_seconds.text)
    # most probably means this incident does not have any delay (e.g. all CLOSURES)
    except AttributeError:
        return -100
