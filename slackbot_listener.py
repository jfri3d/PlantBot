import logging
import os
import re
import time

from slackclient import SlackClient

from constants import RTM_LISTENER_DELAY, MENTION_REGEX

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)

slack_client = SlackClient(os.environ.get("SLACK_BOT_TOKEN"))


def parse_bot_commands(slack_events, bot_id):
    for event in slack_events:
        if event["type"] == "message" and "subtype" not in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == bot_id:
                return message, event["channel"]
    return None, None


def parse_direct_mention(message_text):
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


def handle_status_command(command, channel):
    response = "TODO -> add stuff here"
    slack_client.api_call("chat.postMessage", channel=channel, text=response)


def handle_help_command(command, channel):
    response = "PlantBot only accepts these commands: status, help"
    slack_client.api_call("chat.postMessage", channel=channel, text=response)


# def __send_typing_event(channel):
#     typing_event_json = {"id": 1, "type": "typing", "channel": channel}
#     slack_client.server.send_to_websocket(typing_event_json)


COMMAND_HANDLERS = {
    "status": handle_status_command,
    "help": handle_help_command
}


def handle_command(command, channel):
    logging.info('Handling command "{}"'.format(command))
    handler_func = COMMAND_HANDLERS.get(command, handle_help_command)
    handler_func(command, channel)


if __name__ == "__main__":

    if slack_client.rtm_connect(with_team_state=False):
        logging.info("Listening and running...")

        id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read(), id)
            logging.info(command, channel)
            if command:
                handle_command(command, channel)
            time.sleep(RTM_LISTENER_DELAY)
    else:
        logging.info("Connection failed :(")
