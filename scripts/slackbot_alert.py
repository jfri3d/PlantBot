import inspect
import json
import logging
import os

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from constants import CHANNEL, INTERVAL, EMOJI_LIST, PLANT_DEF
from dotenv import load_dotenv
from slackclient import SlackClient
from utils import latest_data, giphy_grabber

load_dotenv(dotenv_path='.envrc')
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)

slack_client = SlackClient(os.environ.get("SLACK_BOT_TOKEN"))

scheduler = BlockingScheduler()


@scheduler.scheduled_job(CronTrigger(minute='5/{}'.format(INTERVAL), hour='*', day='*', month='*', day_of_week='*'))
def slackbot_alert():
    """
    PlantBot alert via Slack based on which registered plant is below its respective moisture threshold.

    """

    func_name = inspect.stack()[0][3]
    logging.info('[{}] -> Starting Job'.format(func_name))
    if slack_client.rtm_connect(with_team_state=False):

        # load the plant definition file
        with open(PLANT_DEF, 'r') as src:
            plant_def = json.load(src)

        # iterate through plants
        for p in plant_def['plants']:
            logging.info('[{}] -> Checking {}'.format(func_name, p['name']))

            # query latest plant information
            data = latest_data(p['name'], num=1)[0]

            # logic based on moisture
            if data['moisture'] < p['min_moisture']:
                logging.info('[{}] -> Need to water {} [{}%]!!!'.format(func_name, p['name'], data['moisture']))

                # get url for search term for slack
                url = giphy_grabber('water')

                message = '\n:potable_water: *{}* needs water!:potable_water:'.format(p['name'])
                message += '\n\n*Moisture* = {} %'.format(data['moisture'])
                message += '\n*Temperature* = {} °C'.format(data['temperature'])
                message += '\n*Light* = {} lux'.format(data['light'])
                message += '\n*Conductivity* = {} uS/cm'.format(data['conductivity'])
                message += '\n\n{}'.format(url)

                # post message
                resp = slack_client.api_call("chat.postMessage", text=message, channel=CHANNEL)

                for e in EMOJI_LIST:
                    slack_client.api_call("reactions.add", name=e, timestamp=resp['ts'], channel=resp['channel'])
            else:
                logging.info('[{}] -> Healthy moisture ({} %)!'.format(func_name, data['moisture']))
    else:
        logging.info('[{}] -> Connection failed :('.format(func_name))


if __name__ == "__main__":
    scheduler.start()
