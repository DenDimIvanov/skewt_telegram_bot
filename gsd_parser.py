"""
parser for GSD format https://rucsoundings.noaa.gov/raob_format.html
"""
import pandas as pd
import numpy as np


def _knots_to_ms(knots: float) -> float:
    return knots * 0.51444444444


def parse(text: str) -> pd.DataFrame:
    df = None

    if not text:
        return df

    header = 'PRES HGHT TEMP DEWPT WINDDIR WINDSD'
    table = []

    try:
        lines = text.split("\n")

        for line in lines:
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
        return df
