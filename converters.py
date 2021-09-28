from datetime import datetime


def string_to_datetime(string_dt: str) -> datetime:
    if string_dt != "Error":
        return datetime.strptime(string_dt, "%Y-%m-%dT%H:%M:%SZ")
    else:
        return datetime(1970, 1, 1, 0, 0, 0)


# function parsing e.g. current car position from string in input.json
def coordinates_string_to_tuple(coordinates: str) -> tuple:
    lat = float(coordinates.split(",")[0].strip())
    lon = float(coordinates.split(",")[1].strip())
    return lat, lon


def list_from_string(string: str) -> list:
    anything_list = string.split(",")
    return [str(item.strip().upper()) for item in anything_list]
