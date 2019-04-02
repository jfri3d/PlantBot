import logging
import os
import time

from dotenv import load_dotenv
from slackclient import SlackClient
from utils import latest_data

from constants import CHANNEL, RTM_ALERT_DELAY

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)

load_dotenv(dotenv_path='.envrc')
slack_client = SlackClient(os.environ.get("SLACK_BOT_TOKEN"))

if __name__ == "__main__":

    if slack_client.rtm_connect(with_team_state=False):

        logging.info("Starting")

        # query latest plant information
        temperature, moisture, light, conductivity = latest_data()

        # logic for when to water!!!
        while moisture < 30:
            message = 'Water me!\n\nTemp = {} °C\nMoisture = {} %\nLight = {} lux\nConductivity = {} uS/cm'.format(temperature, moisture, light, conductivity)
            logging.info("Posting message to {}".format(CHANNEL))
            slack_client.api_call(
                "chat.postMessage",
                channel=CHANNEL,
                text="@channel {}".format(message),
                link_names=1,
            )

            time.sleep(RTM_ALERT_DELAY)
    else:
        logging.info("Connection failed :(")
