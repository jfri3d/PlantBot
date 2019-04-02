import logging
import os
import time

from dotenv import load_dotenv
from slackclient import SlackClient

from constants import CHANNEL, RTM_ALERT_DELAY, MOISTURE_LIMIT
from utils import latest_data, plot_data

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)

load_dotenv(dotenv_path='.envrc')
slack_client = SlackClient(os.environ.get("SLACK_BOT_TOKEN"))

if __name__ == "__main__":

    if slack_client.rtm_connect(with_team_state=False):

        logging.info("Starting")

        # query latest plant information
        data = latest_data(num=1)[0]

        # logic for when to water!!!
        while data['moisture'] < MOISTURE_LIMIT:
            logging.info("Posting message to {}".format(CHANNEL))
            message = 'Water me!\n\n*Temperature* = {} °C\n*Moisture* = {} %\n*Light* = {} lux\n*Conductivity* = {} uS/cm'.format(
                data['temperature'], data['moisture'], data['light'], data['conductivity'])

            out_path = os.path.join('./ims', "{}.png".format(round(time.time())))
            plot_data(latest_data(num=100), out_path=out_path)

            with open(out_path, "rb") as src:
                slack_client.api_call(
                    "files.upload",
                    channels=CHANNEL,
                    file=src,
                    title='WATER ME!',
                    initial_comment=message,
                )

            time.sleep(RTM_ALERT_DELAY)
    else:
        logging.info("Connection failed :(")
