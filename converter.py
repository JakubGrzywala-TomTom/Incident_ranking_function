from datetime import datetime


def string_to_datetime(string_dt: str) -> datetime:
    if string_dt != "Error":
        return datetime.strptime(string_dt, "%Y-%m-%dT%H:%M:%SZ")
    else:
        return datetime(1970, 1, 1, 0, 0, 0)
