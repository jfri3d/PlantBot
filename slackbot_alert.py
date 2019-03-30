import logging
import os
import time

from dotenv import load_dotenv
from slackclient import SlackClient

from constants import CHANNEL, RTM_ALERT_DELAY, MESSAGE

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)

load_dotenv(dotenv_path='.envrc')
slack_client = SlackClient(os.environ.get("SLACK_BOT_TOKEN"))

if __name__ == "__main__":

    if slack_client.rtm_connect(with_team_state=False):

        logging.info("Starting")

        # TODO -> query plant information

        # TODO -> add logic regarding plant
        while True:
            logging.info("Posting message to {}".format(CHANNEL))
            slack_client.api_call(
                "chat.postMessage",
                channel=CHANNEL,
                text="@channel {}".format(MESSAGE),
                link_names=1,
            )

            time.sleep(RTM_ALERT_DELAY)
    else:
        logging.info("Connection failed :(")
