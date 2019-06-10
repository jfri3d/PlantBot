import inspect
import json
import logging
import math
import os

from PIL import Image, ImageFont, ImageDraw
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from font_fredoka_one import FredokaOne
from inky import InkyWHAT

from constants import THIRSTY_PATH, HEALTHY_PATH, PLANT_DEF, INTERVAL, ASSET_PATH
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
    font = ImageFont.truetype(FredokaOne, 28)
    for ind, p in enumerate(plant_def['plants']):

        logging.info('[{}] -> Updating {}'.format(func_name, p['name']))

        # query latest plant information
        data = latest_data(p['name'], num=1)[0]

        # define placement for plant X
        x = 5  # edge
        y = dy * (ind + 1)
        gap = lambda pct: 2 * math.ceil(dy * pct / 2)

        # add icon
        icon = _load_image(os.path.join(ASSET_PATH, p['icon']), dy - gap(0.2))
        img.paste(icon, box=(x, y + gap(0.2) // 2))

        # add message
        message = "{}     {}%".format(p['name'], int(data['moisture']))
        w, h = font.getsize(message)
        draw.text((dy, y + h // 2), message, inky.BLACK, font)

        # logic based on moisture [different logo]
        if data['moisture'] < p['min_moisture']:
            logging.info('[{}] -> Need to water {} [{}%]!!!'.format(func_name, p['name'], data['moisture']))
            icon = _load_image(THIRSTY_PATH, dy - gap(0.1))
        else:
            logging.info('[{}] -> Healthy moisture ({} %)!'.format(func_name, data['moisture']))
            icon = _load_image(HEALTHY_PATH, dy - gap(0.1))

        # "paste" image
        img.paste(icon, box=(inky.WIDTH - icon.size[0] - x, y + gap(0.1) // 2))

    # display on inky
    inky.set_image(img)
    inky.show()


if __name__ == "__main__":
    scheduler.add_job(inky_update)
    scheduler.start()
