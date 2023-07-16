"""
parser for GSD format https://rucsoundings.noaa.gov/raob_format.html
"""
import pandas as pd
import numpy as np
from typing import List
import datetime


def _knots_to_ms(knots: float) -> float:
    return knots * 0.51444444444


# return 2 values
# 1 - pandas Dataframe with sounding data
# 2 - date forecast of sounding
def parse(text: str):
    df = None
    forecast_date = None

    if not text:
        return df

    header = 'PRES HGHT TEMP DEWPT WINDDIR WINDSD'
    table = []

    try:
        lines = text.split("\n")

        for line_number, line in enumerate(lines):

            if line_number == 1:
                cols = line.strip().split()
                datetime_str = f"{cols[4]},{cols[3]},{cols[2]},{cols[1]}"
                datetime_format = "%Y,%b,%d,%H"
                forecast_date = datetime.datetime.strptime(datetime_str, datetime_format)
            else:
                cols = line.strip().split(" ")
                linetype = cols[0]

            if linetype == "9" or linetype == "4":
                table.append(' '.join(cols[1:]))

        data = [row.split() for row in table]
        df = pd.DataFrame(np.array(data).astype(int), columns=header.split())
        df['PRES'] = df['PRES'].apply(lambda x: x / 10)
        df['TEMP'] = df['TEMP'].apply(lambda x: x / 10)
        df['DEWPT'] = df['DEWPT'].apply(lambda x: x / 10)
        df['WINDSD'] = df['WINDSD'].apply(lambda x: _knots_to_ms(x))

    except Exception as e:
        print(f'Wrong GSD format, caught {type(e)}: e')
    finally:
        return df, forecast_date
