"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import os
import importlib

import yaml

from LRFutils import color

from core import setup_logger

accept = ["y", "yes", "yeah", "ye"]
decline = ["n", "no", "nope", "nah"]

_global_config = {}

logger = setup_logger('config')

# Check basic requirements and start this script if something is missing
def check():
    if not os.path.isfile("config.yaml"):
        print(" ")
        logger.warning("⛔ The bot is not correctly setup. Running setup script...")
        os.system("python3 setup.py")
        exit()


def get(config: str):
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

    with open("core/default_config.yaml", "r", encoding='utf-8') as file:
        _global_config.update(yaml.safe_load(file))

    for plugin in os.listdir("plugins"):
        if os.path.isfile(file := "plugins/" + plugin + "/config.yaml"):
            with open(file, encoding='utf-8') as file:
                _global_config.update({plugin: yaml.safe_load(file)})

    if os.path.isfile("config.yaml"):
        with open("config.yaml", "r", encoding='utf-8') as file:
            _global_config.update(yaml.safe_load(file))

    # Save config
    with open("config.yaml", "w", encoding='utf-8') as file:
        yaml.dump(_global_config, file)


# Automatically load config when the file is imported
if not _global_config:
    reload_config()

################
# Plugin Setup #
################


def setup_plugins():
    """Run the "run" function of each plugin's "setup.py" file in order to allow user to configure
    the plugins.
    Called once in the main setup script."""

    for plugin in os.listdir("plugins"):
        if os.path.isfile("plugins/" + plugin + "/setup.py"):

            plugin_setup = importlib.import_module("plugins." + plugin + ".setup")

            choice = input(
                f"\n{color.fg.blue}🔌 Do you want to configure {plugin} plugin? [Y/n]:{color.stop} "
            )

            if choice.lower() not in decline:
                plugin_config = plugin_setup.run()
                if plugin_config is not None:
                    _global_config.update({plugin: plugin_config})

    # Save config
    with open("config.yaml", "w", encoding='utf-8') as file:
        yaml.dump(_global_config, file)


###############
# TOKEN CHECK #
###############


def token_set(force_set=False):
    """Check if the token is set, if not, ask for it. Return True if the token is set,
    False if not."""

    if _global_config["bot"]["token"] is not None and not force_set:
        choice = input(
            f"\n🔑 {color.fg.blue}A token is already set."\
                f"Do you want to edit it? [y/N]:{color.stop} "
        )
        if choice.lower() not in accept:
            return

    # pylint: disable=line-too-long
    print(
        f"""
🔑 You need to set your Discord bot token in the config file.
   To do so, go on {color.fg.blue}https://discord.com/developers/applications{color.stop}, select your application, go in bot section and copy your token.
   To create a bot application, please refere to this page: {color.fg.blue}https://discord.com/developers/docs/intro{color.stop}.\n   Also, be sure to anable all intents."""
    )

    token = ""
    while token == "":
        token = input(f"\n🔑 {color.fg.blue}Your bot token:{color.stop} ")
        if token == "":
            print(f"\n{color.fg.red}🔑 You need to set a token.{color.stop}")
        else:
            _global_config["bot"]["token"] = token

    with open("config.yaml", "w", encoding='utf-8') as file:
        yaml.dump(_global_config, file)
    return True


#########################
# Advanced config setup #
#########################


def advanced_setup():

    # Language

    lang = "Baguette de fromage"
    language = _global_config["bot"]["default_language"]
    while lang.lower() not in ["en", "fr", ""]:
        lang = input(
            f"\n{color.fg.blue}🌐 Choose your language [en/fr] (current: {language}):{color.stop} "
        )
        if lang.lower() not in ["en", "fr", ""]:
            print(f"{color.fg.red}🌐 Invalid language.{color.stop}")
    if lang != "":
        _global_config["bot"]["default_language"] = lang.lower()

    # Prefix

    prefix = _global_config["bot"]["default_prefix"]
    choice = input(
        f"\n{color.fg.blue}⚜️ Choose the bot command prefix? (current: {prefix}):{color.stop} "
    )
    if choice != "":
        _global_config["bot"]["default_prefix"] = choice

    # Admins

    error = True
    while error:
        error = False
        choice = input(
            f"\n{color.fg.blue}👑 Bot admins"\
                f"(User ID separated with comma. Let empty to ignore):{color.stop} "
        )
        if choice != "":
            admins = choice.replace(" ", "").split(",")
            try:
                _global_config["bot"]["admins"] = [int(admin_id) for admin_id in admins]
            except ValueError:
                print(
                    f"{color.fg.red}👑 Invalid entry. Only user ID (integers),"\
                        f"comma and space are expected.{color.stop}"
                )
                error = True

    # Error channel

    error = True
    while error:
        error = False
        choice = input(
            f"\n{color.fg.blue}🤕 Error channel (Channel ID. Let empty to ignore):{color.stop} "
        )
        if choice != "":
            try:
                channel = int(choice)
                _global_config["bot"]["error_channels"] = channel
            except ValueError:
                print(
                    f"{color.fg.red}🤕 Invalid entry. Only channel ID (integers) are expected."\
                        f"{color.stop}"
                )
                error = True

    with open("config.yaml", "w", encoding='utf-8') as file:
        yaml.dump(_global_config, file)
