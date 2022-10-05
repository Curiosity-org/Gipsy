import yaml
import os
import importlib
from LRFutils.color import Color
from LRFutils import log

accept = ["y", "yes", "yeah", "ye"]
decline = ["n", "no", "nope", "nah"]

_global_config = {}

# Check basic requirements and start this script if something is missing
def check():
    if not os.path.isfile("config.yaml"):
        print(" ")
        log.warn("⛔ The bot is not correctly setup. Running setup script...")
        os.system("python3 setup.py")
        exit()

def get(config:str):
    path = config.split(".")
    conf = _global_config
    for i in path:
        conf = conf[i]
    return conf

#################
# Reload config #
#################

def reload_config():
    """This function read the core/default_config.yaml file and store it in a dictionnary.
    Then, it update the dict' using all the plugins/<plugin>/config.yaml files.
    Finally, it update the dict' using the config.yaml file wich is defined by the user.
    Each step overwrite the previus one."""

    with open("core/default_config.yaml", "r") as f:
        _global_config.update(yaml.safe_load(f))

    for plugin in os.listdir(f'plugins'):
        if os.path.isfile(file := f'plugins/' + plugin + "/config.yaml"):
            with open(file) as f:
                _global_config.update({plugin:yaml.safe_load(f)})

    if os.path.isfile("config.yaml"):
        with open("config.yaml", "r") as f:
            _global_config.update(yaml.safe_load(f))

    # Save config
    with open("config.yaml", "w") as f:
        yaml.dump(_global_config, f)

# Automatically load config when the file is imported
if _global_config == {}:
    reload_config()

################
# Plugin Setup #
################

def setup_plugins():
    """Run the "run" function of each plugin's "setup.py" file in order to allow user to configure the plugins.
    Called once in the main setup script."""

    for plugin in os.listdir(f'plugins'):
        if os.path.isfile(f'plugins/' + plugin + "/setup.py"):

            plugin_setup = importlib.import_module(f"plugins." + plugin + ".setup")

            choice = input(f"\n{Color.Blue}🔌 Do you want to configure {plugin} plugin? [Y/n]:{Color.NC} ")

            if choice.lower() not in decline:
                plugin_config = plugin_setup.run()
                if plugin_config is not None:
                    _global_config.update({plugin:plugin_config})
    
    # Save config
    with open("config.yaml", "w") as f:
        yaml.dump(_global_config, f)

###############
# TOKEN CHECK #
###############

def token_set(force_set = False):
    """Check if the token is set, if not, ask for it. Return True if the token is set, False if not."""

    if _global_config["bot"]["token"] is not None and not force_set:
        choice = input(f"\n🔑 {Color.Blue}A token is already set. Do you want to edit it? [y/N]:{Color.NC} ")
        if choice.lower() not in accept:
            return

    print(f"\n🔑 You need to set your Discord bot token in the config file.\n   To do so, go on {Color.Blue}https://discord.com/developers/applications{Color.NC}, select your application, go in bot section and copy your token.\n   To create a bot application, please refere to this page: {Color.Blue}https://discord.com/developers/docs/intro{Color.NC}.\n   Also, be sure to anable all intents.")
    
    token = ""
    while token == "":
        token = input(f"\n🔑 {Color.Blue}Your bot token:{Color.NC} ")
        if token == "":
            print(f"\n{Color.Red}🔑 You need to set a token.{Color.NC}")
        else:
            _global_config["bot"]["token"] = token

    with open("config.yaml", "w") as f:
        yaml.dump(_global_config, f)
    return True

#########################
# Advanced config setup #
#########################

def advanced_setup():

    # Language 

    lang = "Baguette de fromage"
    language = _global_config["bot"]["default_language"]
    while lang.lower() not in ["en","fr",""]:
        lang = input(f"\n{Color.Blue}🌐 Choose your language [en/fr] (current: {language}):{Color.NC} ")
        if lang.lower() not in ["en","fr",""]:
            print(f"{Color.Red}🌐 Invalid language.{Color.NC}")
    if lang != "":
        _global_config["bot"]["default_language"] = lang.lower()

    # Prefix

    prefix = _global_config["bot"]["default_prefix"]
    choice = input(f"\n{Color.Blue}⚜️ Choose the bot command prefix? (current: {prefix}):{Color.NC} ")
    if choice != "":
        _global_config["bot"]["default_prefix"] = choice

    # Admins

    error = True
    while error:
        error = False
        choice = input(f"\n{Color.Blue}👑 Bot admins (User ID separated with comma. Let empty to ignore):{Color.NC} ")
        if choice != "":
            admins = choice.replace(" ", "").split(",")
            try:
                for admin in admins:
                    admin = int(admin)
                _global_config["bot"]["admins"] = admins
            except:
                print(f"{Color.Red}👑 Invalid entry. Only user ID (integers), comma and space are expected.{Color.NC}")
                error = True

    # Error channel

    error = True
    while error:
        error = False
        choice = input(f"\n{Color.Blue}🤕 Error channel (Channel ID. Let empty to ignore):{Color.NC} ")
        if choice != "":
            try:
                channel = int(choice)
                _global_config["bot"]["error_channels"] = channel
            except:
                print(f"{Color.Red}🤕 Invalid entry. Only channel ID (integers) are expected.{Color.NC}")
    
    with open("config.yaml", "w") as f:
        yaml.dump(_global_config, f)