import inspect
import logging
import os
import sqlite3
from datetime import datetime as dt

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import requests
from astral import Astral
from btlewrap import BluepyBackend
from dateutil import tz
from dotenv import load_dotenv
from miflora.miflora_poller import MiFloraPoller, \
    MI_CONDUCTIVITY, MI_MOISTURE, MI_LIGHT, MI_TEMPERATURE, MI_BATTERY
from mpl_toolkits.axes_grid1 import Grid
from pandas.io.json import json_normalize

load_dotenv(dotenv_path='.envrc')
DB_PATH = 'PlantBot.db'

# deal with timezones
utc_zone = tz.tzutc()
local_zone = tz.tzlocal()

MAC_ADD = os.environ.get("MAC_ADD")
LAT = os.environ.get("LAT")
LON = os.environ.get("LON")
ACCUWEATHER_TOKEN = os.environ.get("ACCUWEATHER_TOKEN")


def get_daylight_hours(lat, lon, today):
    func_name = inspect.stack()[0][3]
    logging.info("[{}] -> Starting Job".format(func_name))

    logging.info('[{}] -> Location: ({}, {})'.format(func_name, lat, lon))

    # get sunrise/sunset times (UTC)

    raw = Astral().sun_utc(today, float(lat), float(lon))

    # convert to local time
    sunrise = raw['sunrise'].replace(tzinfo=utc_zone).astimezone(local_zone)
    sunset = raw['sunset'].replace(tzinfo=utc_zone).astimezone(local_zone)

    logging.info('[{}] -> Sunrise: {}'.format(func_name, sunrise))
    logging.info('[{}] -> Sunset: {}'.format(func_name, sunset))

    return sunrise.hour, sunset.hour


def get_plant_data():
    func_name = inspect.stack()[0][3]
    logging.info("[{}] -> Starting Job".format(func_name))

    poller = MiFloraPoller(MAC_ADD, BluepyBackend)
    logging.info("[{}] -> Getting data from Mi Flora".format(func_name))

    # extract values
    temperature = poller.parameter_value(MI_TEMPERATURE)
    moisture = poller.parameter_value(MI_MOISTURE)
    light = poller.parameter_value(MI_LIGHT)
    conductivity = poller.parameter_value(MI_CONDUCTIVITY)
    battery = poller.parameter_value(MI_BATTERY)

    # write to DB
    logging.info("[{}] -> Writing to DB".format(func_name))
    _insert_data(temperature, moisture, light, conductivity, battery)


def _db_connect():
    if not os.path.isfile(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        _create_table(conn)
    else:
        conn = sqlite3.connect(DB_PATH)
    return conn


def _create_table(conn):
    cur = conn.cursor()  # instantiate a cursor obj

    command = """
        CREATE TABLE plantbot (
            date DATE PRIMARY KEY,
            temperature real NOT NULL,
            moisture real NOT NULL,
            light real NOT NULL,
            conductivity real NOT NULL,
            battery real NOT NULL)"""

    cur.execute(command)
    conn.commit()


def _insert_data(temperature, moisture, light, conductivity, battery):
    conn = _db_connect()  # connect to the database
    cur = conn.cursor()  # instantiate a cursor obj

    command = """INSERT INTO plantbot (date, temperature, moisture, light, conductivity, battery) VALUES (?, ?, ?, ?, ?, ?)"""
    cur.execute(command, (dt.now().strftime("%Y/%m/%d, %H:%M:%S"), temperature, moisture, light, conductivity, battery))
    conn.commit()


def latest_data(num=1):
    conn = _db_connect()  # connect to the database
    cur = conn.cursor()  # instantiate a cursor obj

    command = """SELECT * FROM plantbot ORDER BY date DESC LIMIT {}""".format(num)
    cur.execute(command)
    out = []
    for val in cur.fetchall():
        out.append({'date': val[0],
                    'temperature': val[1],
                    'moisture': val[2],
                    'light': val[3],
                    'conductivity': val[4]})
    return out


def get_forecast():
    response = requests.get(
        'http://dataservice.accuweather.com/locations/v1/cities/geoposition/search',
        params={'q': '{},{}'.format(LAT, LON), 'apikey': ACCUWEATHER_TOKEN},
    )

    loc_key = response.json()['Key']

    response = requests.get(
        'http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/{}'.format(loc_key),
        params={'metric': True, 'apikey': ACCUWEATHER_TOKEN},
    )

    df = json_normalize(response.json())

    return df


# TODO -> interpolate plant data to regular time interval (10 mins?)

# TODO -> de-mean moisture and soil conductivity

# TODO -> build function relating moisture to age + temperature?

# TODO -> predict moisture with forecast temperature

# TODO -> make this pretty!!!


def plot_data(data, out_path):
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'], infer_datetime_format=True)

    plt.close('all')
    fig = plt.figure(figsize=(8, 6), dpi=150)
    ax = Grid(fig, rect=111, nrows_ncols=(4, 1),
              axes_pad=0.1, label_mode='L',
              )

    hours = mdates.HourLocator(interval=12)
    h_fmt = mdates.DateFormatter('%a %-I%p')

    ax[0].plot(df['date'], df['moisture'], '-b', lw=1)
    ax[0].set_ylabel('Moisture [%]', fontsize=10)
    ax[1].plot(df['date'], df['temperature'], '0.7', lw=1)
    ax[1].set_ylabel('Temp [°C]', fontsize=10)
    ax[2].plot(df['date'], df['light'], '0.5', lw=1)
    ax[2].set_ylabel('Light [lux]', fontsize=10)
    ax[3].plot(df['date'], df['conductivity'], '0.3', lw=1)
    ax[3].set_ylabel('Conductivity\n[uS/cm]', fontsize=10)

    ax[3].xaxis.set_major_locator(hours)
    ax[3].xaxis.set_major_formatter(h_fmt)

    fig.autofmt_xdate()

    plt.tight_layout()
    plt.savefig(out_path)
