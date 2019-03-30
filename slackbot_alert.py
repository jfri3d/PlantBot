import os
import time

from slackclient import SlackClient

# instantiate Slack client
slack_client = SlackClient(os.environ.get("SLACK_BOT_TOKEN"))

# starterbot's user ID in Slack: value is assigned after the bot starts up
plantbot_id = None

# constants
RTM_READ_DELAY = 10  # 10 second delay between reading from RTM
CHANNEL = "general"

if __name__ == "__main__":

    if slack_client.rtm_connect(with_team_state=False):

        print("Slackbot alerter connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        plantbot_id = slack_client.api_call("auth.test")["user_id"]

        while True:
            slack_client.api_call(
                "chat.postMessage",
                channel=CHANNEL,
                text="@channel Time to water me!!!",
                link_names=1,
            )

            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
