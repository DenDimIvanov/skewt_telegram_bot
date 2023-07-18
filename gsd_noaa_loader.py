import requests
import gsd_parser as parser
import pandas as pd
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from metpy.plots import SkewT
import numpy as np
import datetime
import tools
import io

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


def query_gsd_sounding_data(lat: float, lon: float, day: datetime.datetime, model='GFS') -> str:
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

    # forecast_offset = tools.get_forecast_offset(day)
    """
    'start_year': day.year, 'start_mday': day.day, 'start_month_name': day.strftime('%b'),
    'start_hour': day.hour, 'start_min': str(0), 'n_hrs': str(1.0),
    """

    parameters = {'airport': str(lat) + ',' + str(lon), 'data_source': model, 'fcst_len': 'shortest',
                  'startSecs': tools.seconds_from_epoc(day.date(), day.hour),
                  'endSecs': tools.seconds_from_epoc(day.date(), day.hour + 1)}

    url = 'https://rucsoundings.noaa.gov/get_soundings.cgi'
    print(f"fetching forecast for forecast_date = {day}")
    text = ""
    try:
        response = requests.get(url, params=parameters)
        # print(response.url)
        if response.status_code != 200:
            raise Exception('Ошибка при выполнении запроса:', response.status_code)
        else:
            text = response.text
    except Exception as e:
        print(e)

    if not text:
        print("не удалось получить прогноз")
    return text


"""
    plot SkewT diagramm. 
    sounding should have columns: PRES   HGHT  TEMP   DEWPT  WINDDIR     WINDSD
    return array of Bytes
"""


def get_skew_fig(sounding: pd.DataFrame, title: str, dpi=300, file_name=None) -> io.BytesIO:
    fig = plt.figure(figsize=(10, 10))
    buf = None
    try:
        skew = SkewT(fig)

        skew.plot(sounding['PRES'], sounding['TEMP'], color='tab:red')
        skew.plot(sounding['PRES'], sounding['DEWPT'], color='tab:green')

        skew.ax.set_ylim(1050, 100)
        skew.ax.set_xlim(-50, 30)

        plt.xlabel('T, Grad Celcius')
        plt.ylabel('Pressure, hPa')
        plt.title(title)

        sounding['U_WIND'], sounding['V_WIND'] = get_wind_components(sounding['WINDSD'],
                                                                     np.deg2rad(sounding['WINDDIR']))
        """
        p = sounding['PRES'].values * units.hPa
        T = sounding['TEMP'].values * units.degC
        Td = sounding['DEWPT'].values * units.degC
        wind_speed = sounding['WINDSD'] * (units.meter/units.second)
        wind_dir = sounding['WINDDIR'].values * units.degrees
        u, v = mpcalc.wind_components(wind_speed, wind_dir)
    
        # Add a secondary axis that automatically converts between pressure and height
        # assuming a standard atmosphere. The value of -0.12 puts the secondary axis
        # 0.12 normalized (0 to 1) coordinates left of the original axis.
        secax = skew.ax.secondary_yaxis(-0.12,
                                        functions=(
                                        lambda p: mpcalc.pressure_to_height_std(units.Quantity(p, 'mbar')).m_as('km'),
                                        lambda h: mpcalc.height_to_pressure_std(units.Quantity(h, 'km')).m))
        secax.yaxis.set_major_locator(plt.FixedLocator([0, 1, 3, 6, 9, 12, 15]))
        secax.yaxis.set_minor_locator(plt.NullLocator())
        secax.yaxis.set_major_formatter(plt.ScalarFormatter())
        secax.set_ylabel('Height (km)')
        """

        skew.plot_barbs(sounding['PRES'], sounding['U_WIND'], sounding['V_WIND'])

        # Add dry adiabats
        skew.plot_dry_adiabats()

        # Add moist adiabats
        skew.plot_moist_adiabats()

        # Add mixing ratio lines
        skew.plot_mixing_lines()

        if file_name:
            fig.savefig(file_name, dpi=dpi)

        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)

    except:
        plt.close(fig)
    finally:
        plt.close(fig)

    if buf:
        return buf.getvalue()
    else:
        return None


"""
if __name__ == "__main__":
    
    lat = 54.41
    lon = 38.1

    text = query_gsd_sounding_data(lat, lon, datetime.datetime(2023, 7, 19, 9, 0, 0))
    print(text)

    sounding, forecast_date = parser.parse(text)
    print(sounding)
    print(forecast_date)

    title = f"For lon={lon}, lat={lat} on {forecast_date} UTC"

    bytes_array = get_skew_fig(sounding, title, 300, 'test.png')
"""
