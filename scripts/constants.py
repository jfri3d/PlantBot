# define fixed rate for running plantbot.py
INTERVAL = 20

# define slack channel + emojis
CHANNEL = "general"
EMOJI_LIST = ["herb", "seedling", "leaves", "fallen_leaf"]

# plant definition file
PLANT_DEF = './data/plant_def.json'
DB_PATH = './data/plantbot.sqlite'

# images
LOGO_PATH = './assets/plant.png'
HEALTHY_PATH = './assets/healthy.jpg'
THIRSTY_PATH = './assets/thirsty.png'

# slackbot
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
