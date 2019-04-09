import inspect
import logging
import os

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from slackclient import SlackClient

from constants import CHANNEL, INTERVAL, MOISTURE_MIN, MOISTURE_MAX
from utils import latest_data, giphy_grabber

load_dotenv(dotenv_path='.envrc')
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)

slack_client = SlackClient(os.environ.get("SLACK_BOT_TOKEN"))

scheduler = BlockingScheduler()


@scheduler.scheduled_job(CronTrigger(minute='5/{}'.format(INTERVAL), hour='*', day='*', month='*', day_of_week='*'))
def slackbot_alert():
    func_name = inspect.stack()[0][3]
    logging.info('[{}] -> Starting Job'.format(func_name))
    if slack_client.rtm_connect(with_team_state=False):

        # query latest plant information
        data = latest_data(num=1)[0]

        # logic based on moisture
        if not MOISTURE_MIN < data['moisture'] < MOISTURE_MAX:
            logging.info('[{}] -> Posting message to {}'.format(func_name, CHANNEL))

            # get url for search term for slack
            url = giphy_grabber('water')

            message = ':potable_water: Please Water me!:potable_water:'
            message += '\n*Moisture* = {} %'.format(data['moisture'])
            message += '\n*Temperature* = {} °C'.format(data['temperature'])
            message += '\n*Light* = {} lux'.format(data['light'])
            message += '\n*Conductivity* = {} uS/cm'.format(data['conductivity'])
            message += '\n\n{}'.format(url)

            # post message
            slack_client.api_call("chat.postMessage", channel=CHANNEL, text=message)

        else:
            logging.info('[{}] -> Healthy moisture ({} %)!'.format(func_name, data['moisture']))
    else:
        logging.info('[{}] -> Connection failed :('.format(func_name))


if __name__ == "__main__":
    scheduler.start()
