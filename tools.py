import datetime
import os
from typing import List, Optional

_epoc = datetime.datetime(1977, 1, 1)
_update_times = [0, 6, 12, 18]
_forecast_offsets = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 18, 24, 36, 48, 60, 72, 84, 96, 108, 120, 144, 168, 192]


def seconds_from_epoc(day: datetime.date, hours: int = 0) -> int:
    if not day:
        print("From seconds_rom_epoc: day is not recognized")
        return None
    else:
        dt = datetime.datetime(day.year, day.month, day.day, hours)
        diff = dt - _epoc
        return int(diff.total_seconds())

def find_nearest(given:int, arr:List[int])->Optional[int]:
    smallests = [num for num in arr if num<given]
    nearest = max(smallests) if smallests else None
    return nearest

def get_forecast_offset(requested_time:datetime.datetime):
    current_time = datetime.datetime.utcnow()

    offset = (requested_time - current_time).total_seconds()/3600
    if offset < 0:
        print("date in the past")
        return None


    #last update of forecast hours
    hour_of_latest_forecast_update = find_nearest(current_time.hour, _update_times)
    offset += current_time.hour - hour_of_latest_forecast_update

    #find nearest forecast offset
    offset = find_nearest(offset, _forecast_offsets)

    return offset


if __name__ == '__main__':
    forecast_date = datetime.datetime(2023, 7, 17, 9, 0, 0)
    print(datetime.datetime.utcnow().hour)
    print(forecast_date.hour)
    print(get_forecast_offset(forecast_date))

    str = "GFS         6      16      Jul    2023"
    cols = str.strip().split()
    print(cols)
    datetime_str = f"{cols[4]},{cols[3]},{cols[2]},{cols[1]}"
    print(datetime_str)
    datetime_format = "%Y,%b,%d,%H"
    forecast_date = datetime.datetime.strptime(datetime_str, datetime_format)
    print(forecast_date)