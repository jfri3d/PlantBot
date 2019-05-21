import json
import os
import re
import time

from dateutil import tz
from dotenv import load_dotenv
from slackclient import SlackClient

from constants import RTM_READ_DELAY, MENTION_REGEX, PLANT_DEF
from utils import latest_data

load_dotenv(dotenv_path='.envrc')

# deal with timezones
from_zone = tz.tzutc()
to_zone = tz.gettz('Europe/Berlin')

# instantiate Slack client
slack_client = SlackClient(os.environ.get("SLACK_BOT_TOKEN"))

# starterbot's user ID in Slack: value is assigned after the bot starts up
plantbot_id = None


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and "subtype" not in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == plantbot_id:
                return message, event["channel"]
    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


def handle_info_command(command, channel):
    # load the plant definition file
    with open(PLANT_DEF, 'r') as src:
        plant_def = json.load(src)

    # iterate through plants
    for p in plant_def['plants']:
        # query latest plant information
        data = latest_data(p['name'], num=1)[0]

        message = '*{}* info [{}]:\n'.format(p['name'], data['date'])
        message += '===========================\n'
        message += '*Moisture* = {} %\n'.format(data['moisture'])
        message += '*Temperature* = {} °C\n'.format(data['temperature'])
        message += '*Light* = {} lux\n'.format(data['light'])
        message += '*Conductivity* = {} uS/cm\n\n'.format(data['conductivity'])

        slack_client.api_call("chat.postMessage", channel=channel, text=message)


def handle_help_command(command, channel):
    response = "Try one of the following commands: {}".format(", ".join(list(COMMAND_HANDLERS.keys())))
    slack_client.api_call("chat.postMessage", channel=channel, text=response)


def __send_typing_event(channel):
    typing_event_json = {"id": 1, "type": "typing", "channel": channel}
    slack_client.server.send_to_websocket(typing_event_json)


COMMAND_HANDLERS = {
    "info": handle_info_command,
    "help": handle_help_command
}


def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    print('Handling command "{}"'.format(command))
    handler_func = COMMAND_HANDLERS.get(command, handle_help_command)
    handler_func(command, channel)


if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("PlantBot is alive")
        # Read bot's user ID by calling Web API method `auth.test`
        plantbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
