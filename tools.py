import datetime
from typing import List, Optional
from metpy.units import units


_epoc = datetime.datetime(1970, 1, 1)
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
    date = datetime.datetime(2023, 7, 18, 9)
    day = datetime.date(2023, 7, 18)

    print(seconds_from_epoc(day, 9))

    print(seconds_from_epoc(date.date(), 9))
    print(seconds_from_epoc(date + datetime.timedelta(hours=1)))
    print(units.degC)