import json, os
from shutil import copyfile

def get_config(path: str, isBotConfig: bool):
    if not os.path.isfile(path + ".json"):
        copyfile(path + '-example.json', path + '.json')
        if isBotConfig:
            print("TOKEN MISSING: Please, enter your bot token in the config/config.json and restart the bot.")
            return None
    with open(path + ".json") as f:
        conf = json.load(f)
    if isBotConfig:
        if conf["token"] == "Discord token for main bot":
            print("TOKEN MISSING: Please, enter your bot token in the config/config.json and restart the bot.")
            return None
    return conf