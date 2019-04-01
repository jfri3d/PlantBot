import inspect
import logging
import os
import sqlite3
from datetime import datetime as dt

from astral import Astral
from btlewrap import BluepyBackend
from dateutil import tz
from dotenv import load_dotenv
from miflora.miflora_poller import MiFloraPoller, \
    MI_CONDUCTIVITY, MI_MOISTURE, MI_LIGHT, MI_TEMPERATURE, MI_BATTERY

load_dotenv(dotenv_path='.envrc')
DB_PATH = 'PlantBot.db'

# deal with timezones
utc_zone = tz.tzutc()
local_zone = tz.tzlocal()

MAC_ADD = os.environ.get("MAC_ADD")


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
