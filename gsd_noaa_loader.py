import requests
import gsd_parser as parser
import pandas as pd
import matplotlib.pyplot as plt
from metpy.plots import SkewT
import numpy as np

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

url = "https://rucsoundings.noaa.gov/get_soundings.cgi?data_source=GFS&start_year=2023&start_month_name=Jul&start_mday=14&start_hour=9&start_min=0&n_hrs=1.0&fcst_len=shortest&airport=55.7%2C37.6&text=Ascii%20text%20%28GSL%20format%29&hydrometeors=false&startSecs=1689325200&endSecs=1689328800"

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

sounding = parser.parse(text)



fig = plt.figure(figsize=(10, 10))
skew = SkewT(fig)

skew.plot(sounding['PRES'], sounding['TEMP'], color='tab:red')
skew.plot(sounding['PRES'], sounding['DEWPT'], color='tab:green')


skew.ax.set_ylim(1050, 100)
skew.ax.set_xlim(-50, 20)

plt.xlabel('T, Grad Celcius')
plt.ylabel('Pressure, hPa')
plt.title('Кончинка, 17 июля, 9am UTC')



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

fig.savefig('test.png', dpi=300)





