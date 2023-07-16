import requests
import gsd_parser as parser
import pandas as pd
import matplotlib.pyplot as plt
from metpy.plots import SkewT
import numpy as np
import datetime
import tools

_models = ['GFS', 'NAM', 'Op40']


def get_wind_components(speed, wdir):
    r"""Calculate the U, V wind vector components from the speed and direction.

    Parameters
    ----------
    speed : array_like
        The wind speed (magnitude)
    wdir : array_like
        The wind direction, specified as the direction from which the wind is
        blowing, with 0 being North.

    Returns
    -------
    u, v : tuple of array_like
        The wind components in the X (East-West) and Y (North-South)
        directions, respectively.

    """
    u = -speed * np.sin(wdir)
    v = -speed * np.cos(wdir)
    return u, v


"""
prepare request and query sounding data from noaa service 
for details see https://rucsoundings.noaa.gov/text_sounding_query_parameters.pdf
"""


def query_gsd_sounding_data(lon: float, lat: float, day: datetime.datetime, model='GFS') -> str:
    # verify lon and lat parameters
    if not (lon > -90 and lon < 90):
        raise Exception("invalid longitute")
    if not (lat > -180 and lat < 180):
        raise Exception("invalid latitute")

    # verify day parameter
    # TODO

    # verify model paramenter
    if not model in _models:
        raise Exception("Unknown model")

    forecast_offset = tools.get_forecast_offset(day)

    parameters = {'airport': str(lon) + ',' + str(lat), 'data_source': model, 'fcst_len': forecast_offset,
                  'latest': 'latest', 'start': 'latest'}
    url = 'https://rucsoundings.noaa.gov/get_soundings.cgi'

    text = ""
    try:
        response = requests.get(url, params=parameters)
        print(response.url)
        if response.status_code != 200:
            raise Exception('Ошибка при выполнении запроса:', response.status_code)
        else:
            text = response.text
    except Exception as e:
        print(e)

    if not text:
        print("не удалось получить прогноз")
    return text


"https://rucsoundings.noaa.gov/get_soundings.cgi?data_source=GFS&latest=latest&fcst_len=36&airport=55.7%2C37.6&start=latest"

"""
url = "https://rucsoundings.noaa.gov/get_soundings.cgi?data_source=GFS&airport=55.7%2C37.6&startSecs=1689325200&endSecs=1689328800"

text = ""
try:
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception('Ошибка при выполнении запроса:', response.status_code)
    else:
        text = response.text
except Exception as e:
    print(e)

if not text:
    print("не удалось получить прогноз")
    exit()
"""


def get_skew_fig(sounding: pd.DataFrame, title: str, dpi=300, file_name=None) -> plt.Figure:
    fig = plt.figure(figsize=(10, 10))
    skew = SkewT(fig)

    skew.plot(sounding['PRES'], sounding['TEMP'], color='tab:red')
    skew.plot(sounding['PRES'], sounding['DEWPT'], color='tab:green')

    skew.ax.set_ylim(1050, 100)
    skew.ax.set_xlim(-50, 20)

    plt.xlabel('T, Grad Celcius')
    plt.ylabel('Pressure, hPa')
    plt.title(title)

    sounding['U_WIND'], sounding['V_WIND'] = get_wind_components(sounding['WINDSD'],
                                                                 np.deg2rad(sounding['WINDDIR']))

    print(sounding)

    skew.plot_barbs(sounding['PRES'], sounding['U_WIND'], sounding['V_WIND'])

    # Add dry adiabats
    skew.plot_dry_adiabats()

    # Add moist adiabats
    skew.plot_moist_adiabats()

    # Add mixing ratio lines
    skew.plot_mixing_lines()

    if file_name:
        fig.savefig(file_name, dpi=dpi)

    return fig


if __name__ == "__main__":
    lon = 55.7
    lat = 37.6

    text = query_gsd_sounding_data(lon, lat, datetime.datetime(2023, 7, 17, 9, 0, 0))
    print(text)

    sounding, forecast_date = parser.parse(text)
    print(sounding)
    print(forecast_date)

    title = f"For lon={lon}, lat={lat} on {forecast_date} UTC"

    fig = get_skew_fig(sounding, title, 300, 'test.png')
