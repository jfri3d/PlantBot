import inspect
import json
import logging
import os
import random
import sqlite3
from datetime import datetime as dt

import giphypop
from PIL import Image, ImageFont
from astral import Astral
from btlewrap import BluepyBackend, BluetoothBackendException
from constants import DB_PATH, PLANT_DEF, LOGO_PATH
from dateutil import tz
from dotenv import load_dotenv
from font_fredoka_one import FredokaOne
from miflora.miflora_poller import MiFloraPoller, \
    MI_CONDUCTIVITY, MI_MOISTURE, MI_LIGHT, MI_TEMPERATURE, MI_BATTERY

load_dotenv(dotenv_path='.envrc')

# deal with timezones
utc_zone = tz.tzutc()
local_zone = tz.tzlocal()

LAT = os.environ.get("LAT")
LON = os.environ.get("LON")
GIPHY_KEY = os.environ.get("GIPHY_KEY")


def get_daylight_hours(lat, lon, today):
    """
    Function for determining the sunrise and sunset hours (in UTC) based on a geolocation.
    Note that the UTC times are converted to local time.

    Args:
        lat (float): latitude
        lon (float): longitude
        today (obj): datetime python object

    Returns:
        <sunrise>, <sunset>

    """
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
    """
    Main function for extracting current plant measurements (per plant).

    """
    func_name = inspect.stack()[0][3]
    logging.info("[{}] -> Starting Job".format(func_name))

    # load the plant definition file
    with open(PLANT_DEF, 'r') as src:
        plant_def = json.load(src)

    # iterate through plants
    for p in plant_def['plants']:
        try:
            # connect -> get data
            logging.info("[{}] -> Getting data from Mi Flora [{}]".format(func_name, p['name']))
            poller = MiFloraPoller(p['mac_address'], BluepyBackend)

            # write to DB
            logging.info("[{}] -> Writing to DB [{}]".format(func_name, p['name']))
            _insert_data(p['name'], poller)
        except BluetoothBackendException:
            logging.error("[{}] -> BlueToothBackendException [{}]".format(func_name, p['name']))


def _insert_data(plant_name, poller):
    """
    Anonymous function for storing plant measurements to a local sqlite DB.

    Args:
        plant_name (str): name of plant for writing to correct table
        poller (obj): miflora object containing measurements

    """
    # connect to the database
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # check if table exists
    if not _check_table(conn, plant_name):
        _create_table(conn, plant_name)

    # extract values for plant
    temperature = poller.parameter_value(MI_TEMPERATURE)
    moisture = poller.parameter_value(MI_MOISTURE)
    light = poller.parameter_value(MI_LIGHT)
    conductivity = poller.parameter_value(MI_CONDUCTIVITY)
    battery = poller.parameter_value(MI_BATTERY)

    command = """
        INSERT INTO {} (
            date,
            temperature,
            moisture,
            light,
            conductivity,
            battery)
        VALUES (?, ?, ?, ?, ?, ?)""".format(plant_name)
    cur.execute(command, (dt.now().strftime("%Y/%m/%d, %H:%M:%S"), temperature, moisture, light, conductivity, battery))
    conn.commit()


def _check_table(conn, plant_name):
    """
    Utility to check if table exists in the DB connection.

    Args:
        conn (obj): database connection (sqlite)
        plant_name (str): name of plant for writing to correct table

    """
    command = """
            SELECT 1 FROM sqlite_master WHERE type='table' and name = ?"""
    check = conn.execute(command, (plant_name,)).fetchone()
    return check is not None


def _create_table(conn, plant_name):
    """
    Utility for creating table in DB based on fixed schema (based on sensor output).

    Args:
        conn (obj): database connection (sqlite)
        plant_name (str): name of plant for writing to correct table

    """
    cur = conn.cursor()  # instantiate a cursor obj

    command = """
        CREATE TABLE {} (
            date DATE PRIMARY KEY,
            temperature real NOT NULL,
            moisture real NOT NULL,
            light real NOT NULL,
            conductivity real NOT NULL,
            battery real NOT NULL)""".format(plant_name)

    cur.execute(command)
    conn.commit()


def latest_data(plant_name, num=1):
    """
    Function for extracting the lastest plant measurements (by time).

    Args:
        plant_name (str): name of plant for writing to correct table
        num (int): number of latest measurements to extract for analysis

    Returns:
        out (list): contains a list of dictionaries containing plant measurements

    """
    conn = sqlite3.connect(DB_PATH)  # connect to the database
    cur = conn.cursor()  # instantiate a cursor obj

    command = """SELECT * FROM {} ORDER BY date DESC LIMIT {}""".format(plant_name, num)
    cur.execute(command)
    out = []
    for val in cur.fetchall():
        out.append({'date': val[0],
                    'temperature': val[1],
                    'moisture': val[2],
                    'light': val[3],
                    'conductivity': val[4]})
    return out


def giphy_grabber(search, limit=100):
    """
    Utility for connecting and saving a random gif from the giphy API based on a search term.

    Args:
        search (str): search term for querying API
        limit (int): maximum number of results to return

    Returns:
        url (str): url of randomly selected gif

    """

    # call giphy
    g = giphypop.Giphy(api_key=GIPHY_KEY)

    # search based on keyword
    gen = g.search(search.replace('_', ' '), limit=limit)

    # get random
    choice = random.randint(0, limit)
    ii = 0
    while ii != choice:
        url = next(gen)
        ii += 1

    return url


# get water drop
def _load_image(path, dy):

    # open image
    im = Image.open(path)

    # keep aspect ratio
    ratio = im.size[0]/im.size[1]
    im = im.resize((int(ratio*dy), dy), resample=Image.LANCZOS)

    # build appropriate INKY palette
    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette((255, 255, 255, 0, 0, 0, 255, 0, 0) + (0, 0, 0) * 252)

    return im.convert("RGB").quantize(palette=pal_img)


def _calculate_spacing(inky, n):
    return inky.HEIGHT // (n + 1)


def _build_header(inky, draw, img, n):
    # build grid for showing information
    dy = _calculate_spacing(inky, n)
    for ind in range(n):
        y = dy * (ind + 1)
        draw.line((0, y, inky.WIDTH, y), fill=inky.BLACK, width=2)

    # add PlantBot icon
    logo = _load_image(LOGO_PATH, dy)
    img.paste(logo, box=(0, (dy - logo.size[1]) // 2))

    # format message for inkyWHAT
    header = "PlantBot"
    font = ImageFont.truetype(FredokaOne, 32)
    w, h = font.getsize(header)
    y = dy // 2 - h // 2
    draw.text((logo.size[0], y), header, inky.BLACK, font)

    # include date/time of last "run"
    header = dt.now().strftime("%d.%m.%Y %H:%M")
    font = ImageFont.truetype(FredokaOne, 16)
    w, h = font.getsize(header)
    time_edge = 2
    draw.text((inky.WIDTH - w - time_edge, 0), header, inky.BLACK, font)

    return img
