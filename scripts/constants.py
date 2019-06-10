import os

# define fixed rate for running plantbot.py
INTERVAL = 5

# define slack channel + emojis
CHANNEL = "general"
EMOJI_LIST = ["herb", "seedling", "leaves", "fallen_leaf"]

# plant definition file
PLANT_DEF = './data/plant_def.json'
DB_PATH = './data/plantbot.sqlite'

# images
ASSET_PATH = './assets'
LOGO_PATH = os.path.join(ASSET_PATH, 'plant.png')
HEALTHY_PATH = os.path.join(ASSET_PATH, 'healthy.jpg')
THIRSTY_PATH = os.path.join(ASSET_PATH, 'thirsty.png')

# slackbot
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
