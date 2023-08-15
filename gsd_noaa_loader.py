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
    if not (lat > -90 and lat < 90):
        raise Exception("invalid longitute")
    if not (lon > -180 and lon < 180):
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


"""
    plot SkewT diagramm. 
    sounding should have columns: PRES   HGHT  TEMP   DEWPT  WINDDIR     WINDSD
    return array of Bytes
"""
def get_skew_fig(sounding: pd.DataFrame, title: str, dpi=300, file_name=None) -> io.BytesIO:
    fig = plt.figure(figsize=(10, 10))
    buf = None
    try:
        skew = SkewT(fig, rotation=45)


        skew.plot(sounding['PRES'], sounding['TEMP'], color='tab:red')
        skew.plot(sounding['PRES'], sounding['DEWPT'], color='tab:green')

        skew.ax.set_ylim(1000, 50)
        skew.ax.set_xlim(-50, 30)

        plt.xlabel('T, Grad Celcius')
        plt.ylabel('Pressure, hPa, m')

        plt.title(title)

        sounding['U_WIND'], sounding['V_WIND'] = get_wind_components(sounding['WINDSD'],
                                                                     np.deg2rad(sounding['WINDDIR']))
        skew.plot_barbs(sounding['PRES'], sounding['U_WIND'], sounding['V_WIND'])

        for p, w, h in zip(sounding['PRES'], sounding['WINDSD'], sounding['HGHT']):
            if p >= 100:
                print(f"p={p}  w={w}  h={h}")
                skew.ax.text(1.03, p, round(w, 1), transform=skew.ax.get_yaxis_transform(which='tick2'))
                skew.ax.text(0.01, p, round(h, 0), transform=skew.ax.get_yaxis_transform(which='tick2'))

        # Add dry adiabats
        skew.plot_dry_adiabats()

        # Add moist adiabats
        skew.plot_moist_adiabats()

        # Add mixing ratio lines
        skew.plot_mixing_lines()


        #temp gradient
        sounding['D_T'] = sounding['TEMP'].diff().fillna(0)
        sounding['D_H'] = sounding['HGHT'].diff().fillna(0)
        sounding['GRADT'] = (sounding['D_T'] / sounding['D_H']).fillna(0)



        if file_name:
            fig.savefig(file_name, dpi=dpi)

        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)

    except Exception as e:
        print(e)
    finally:
        plt.close(fig)

    if buf:
        return buf.getvalue()
    else:
        return None

def get_skewt(lat: float, lon: float, forecast_date: datetime.datetime, file_name=None):
    text = query_gsd_sounding_data(lat, lon, forecast_date)

    print("got sounding data from noaa. start gsd parsing")

    print(text)

    sounding, forecast_date = parser.parse(text)


    print("gsd parsing complete. start plotting")

    title = f"For lat={lat}, lon={lon} on {forecast_date} UTC"

    bytes_array = get_skew_fig(sounding, title, 300, file_name)
    return bytes_array




if __name__ == "__main__":
    """
    lat = 54.41
    lon = 38.1
    date = datetime.datetime(2023, 8, 8, 9, 0, 0)
    text_forecast_data = query_gsd_sounding_data(lat, lon, date)
    df_sounding, dt_forecast_date = parser.parse(text_forecast_data)
    df_sounding.to_csv('df.sounding_test_data.csv')
    """

    df_sounding = pd.read_csv('df.sounding_test_data.csv')
    df_sounding['D_T'] = df_sounding['TEMP'].diff().fillna(0)
    df_sounding['D_H'] = df_sounding['HGHT'].diff().fillna(0)
    df_sounding['GRADT'] = (df_sounding['D_T'] / df_sounding['D_H']).fillna(0)


    print(df_sounding)
    #get_skew_fig_new(df_sounding, 'test ', 300, 'test.png')

    # get_skewt(lat, lon, datetime.datetime(2023, 7, 19, 9, 0, 0), 'test.png')
