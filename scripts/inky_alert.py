import inspect
import json
import logging
import math
import os
from datetime import datetime as dt

from PIL import Image, ImageFont, ImageDraw
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from font_fredoka_one import FredokaOne
from inky import InkyWHAT

from constants import THIRSTY_PATH, HEALTHY_PATH, PLANT_DEF, INTERVAL, SUN_PATH, MOON_PATH, MAX_LUX, PLANT_ICON_PATH
from utils import latest_data, _build_header, _calculate_spacing, _load_image

load_dotenv(dotenv_path='.envrc')
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)

scheduler = BlockingScheduler()


@scheduler.scheduled_job(CronTrigger(minute='1/{}'.format(INTERVAL), hour='*', day='*', month='*', day_of_week='*'))
def inky_update():
    """
    PlantBot update via inkyWHAT based on which registered plant is below its respective moisture threshold.

    """

    func_name = inspect.stack()[0][3]
    logging.info('[{}] -> Starting Job'.format(func_name))

    # initialize inky
    inky = InkyWHAT("black")
    inky.set_border(inky.BLACK)

    # draw empty image
    img = Image.new("P", (inky.WIDTH, inky.HEIGHT))
    draw = ImageDraw.Draw(img)

    # load the plant definition file
    with open(PLANT_DEF, 'r') as src:
        plant_def = json.load(src)

    # determine number of plants
    n = len(plant_def['plants'])

    # build header
    img = _build_header(inky, draw, img, n)

    # determine spacing
    dy = _calculate_spacing(inky, n)

    # iterate through plants
    font = lambda fs: ImageFont.truetype(FredokaOne, fs)
    name_font = font(25)
    time_font = font(12)
    val_font = font(20)
    for ind, p in enumerate(plant_def['plants']):

        logging.info('[{}] -> Updating {}'.format(func_name, p['name']))

        # query latest plant information
        data = latest_data(p['name'], num=1)[0]

        # define placement for plant X
        edge = 5  # edge
        y = dy * (ind + 1)
        gap = lambda pct: 2 * math.ceil(dy * pct / 2)

        # add icon
        icon = _load_image(os.path.join(PLANT_ICON_PATH, p['icon']), dy - gap(0.2))
        img.paste(icon, box=(edge, y + gap(0.2) // 2))

        # add name
        message = p['name']
        w, h = name_font.getsize(message)
        loc = y + dy // 2 - h // 2
        draw.text((dy + edge, loc - edge), message, inky.BLACK, name_font)

        # add measurement time
        message = dt.strptime(data['date'], "%Y/%m/%d, %H:%M:%S").strftime("%d.%m.%Y %H:%M")
        w, h = time_font.getsize(message)
        time_edge = 2
        draw.text((dy + edge, y + dy - h - time_edge), message, inky.BLACK, time_font)

        # add vertical line
        draw.line((200, y, 200, y + dy), fill=inky.BLACK, width=2)

        # add moisture information
        message = "{}%".format(int(data['moisture']))
        w, h = val_font.getsize(message)
        loc = y + dy // 2 - h // 2
        draw.text((200 + edge, loc - edge), message, inky.BLACK, val_font)

        # logic based on moisture [different logo]
        if data['moisture'] < p['min_moisture']:
            logging.info('[{}] -> Need to water {} [{}%]!!!'.format(func_name, p['name'], data['moisture']))
            icon = _load_image(THIRSTY_PATH, dy - gap(0.1))
        else:
            logging.info('[{}] -> Healthy moisture ({} %)!'.format(func_name, data['moisture']))
            icon = _load_image(HEALTHY_PATH, dy - gap(0.1))

        # "paste" image
        img.paste(icon, box=(250 + dy // 2 - icon.size[0] // 2, y + gap(0.1) // 2))

        # add vertical line
        draw.line((300, y, 300, y + dy), fill=inky.BLACK, width=2)

        # add temperature/light information
        message = "{}°C".format(int(data['temperature']))
        w, h = val_font.getsize(message)
        loc = y + dy // 2 - h // 2
        draw.text((300 + edge, loc - edge), message, inky.BLACK, val_font)

        # logic based on light [different logo + scaling]
        dy_sun = 0
        if data['light'] < 10:
            icon = _load_image(MOON_PATH, dy - gap(0.1))
        else:
            sun_size = max([gap(0.1), dy - int((math.log(MAX_LUX) - math.log(data['light'])) * 6)])
            icon = _load_image(SUN_PATH, sun_size)
            dy_sun = dy // 2 - icon.size[1] // 2

        # "paste" image
        img.paste(icon, box=(350 + dy // 2 - icon.size[0] // 2, y + dy_sun + gap(0.1) // 2))

    # display on inky
    inky.set_image(img)
    inky.show()


if __name__ == "__main__":
    scheduler.add_job(inky_update)
    scheduler.start()
