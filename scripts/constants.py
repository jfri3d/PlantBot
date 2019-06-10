import os

# define fixed rate for running plantbot.py
INTERVAL = 10

# define slack channel + emojis
CHANNEL = "general"
EMOJI_LIST = ["herb", "seedling", "leaves", "fallen_leaf"]

# plant definition file
PLANT_DEF = './data/plant_def.json'
DB_PATH = './data/plantbot.sqlite'

# general images
ASSET_PATH = './assets'
PLANT_ICON_PATH = os.path.join(ASSET_PATH, 'plant_icons')
LOGO_PATH = os.path.join(ASSET_PATH, 'logo.png')

# moisture icons
MOISTURE_ICON_PATH = os.path.join(ASSET_PATH, 'moisture_icons')
HEALTHY_PATH = os.path.join(MOISTURE_ICON_PATH, 'healthy.jpg')
THIRSTY_PATH = os.path.join(MOISTURE_ICON_PATH, 'thirsty.png')

# light icons
MAX_LUX = 107527  # as per -> https://www.engineeringtoolbox.com/light-level-rooms-d_708.html
LIGHT_ICON_PATH = os.path.join(ASSET_PATH, 'light_icons')
SUN_PATH = os.path.join(LIGHT_ICON_PATH, 'sun.png')
MOON_PATH = os.path.join(LIGHT_ICON_PATH, 'moon.jpg')

# slackbot
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
