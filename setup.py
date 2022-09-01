import os
import shutil
from tkinter import N
from LRFutils.color import Color
from LRFutils import log
from core import config
import yaml
import importlib

accept = ["y", "yes", "yeah", "ye"]
decline = ["n", "no", "nope", "nah"]

# Check basic requirements and start this script if something is missing
def check():
    if not os.path.isfile("config.yaml"):
        print(" ")
        log.warn("⛔ The bot is not correctly setup. Running setup script...")
        os.system("python3 setup.py")
        exit()

###############
# TOKEN CHECK #
###############

def token_set(force_set = False):
    """Check if the token is set, if not, ask for it. Return True if the token is set, False if not."""

    if config.global_config["bot"]["token"] is not None and not force_set:
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
            config.global_config["bot"]["token"] = token

    if config.global_config["bot"]["token"] is None:
        # Explain how to get a token
        print(f"\n🔑 You need to set your Discord bot token in the config file.\n   To do so, go on {Color.Blue}https://discord.com/developers/applications{Color.NC}, select your application, go in bot section and copy your token.\n   To create a bot application, please refere to this page: {Color.Blue}https://discord.com/developers/docs/intro{Color.NC}.\n   Also, be sure to anable all intents.\n")
        
        # Create the config.py file if it doesn't exist
        if not os.path.isfile("config.py"):
            with open("config.py", "w+") as conf_file:
                conf_file.write("from core.default_config import *\n")

        # Ask for the token and save it in config.py
        with open("config.py", "a") as conf_file:
            token = input(f"{Color.Blue}🔑 Paste your token here (let empty and press 'enter' to ignore):{Color.NC} ")
            if token == "":
                print(f"\n{Color.Red}❌ Setup uncomplete 🙁{Color.NC}")
                return False
            conf_file.write(f"\nbot.token = '{token}'\n")
    return True

################
# Plugin Setup #
################

def plugin_setup():
    for plugin in os.listdir(f'plugins'):
        if os.path.isfile(f'plugins/' + plugin + "/setup.py"):

            plugin_setup = importlib.import_module(f"plugins." + plugin + ".setup")

            choice = input(f"\n{Color.Blue}🔌 Do you want to configure {plugin} plugin? [Y/n]:{Color.NC} ")

            if choice not in decline:
                plugin_setup.run()

########################
# INSTALL DEPENDENCIEs #
########################

def install_dependencies():
    """Install all dependencies needed for the bot to work."""

    choice = input(f"\n🏗️ You need to install the bot dependencies. The automatic script will probably upgrade (or rarely downgrade) some python modules already installed on your machine.\n{Color.Blue}\n🏗️ Do you want to install dependencies? [y/N]{Color.NC}")
    if choice.lower() in accept:
        print("🏗️ Installing dependencies...")
        os.system("python3 -m pip install -r requirements.txt")
    else:
        print("   Dependencies not installed.")

if __name__ == "__main__":

    config.reload_config()

    install_dependencies()

    token_set()

    # Optional settings

    choice = input(f"\n{Color.Blue}Do you want to configure optional bot settings? [Y/n]:{Color.NC} ")

    if choice not in decline:

        # Language 

        lang = "Baguete de fromage"
        language = config.global_config["bot"]["default_language"]
        while lang.lower() not in ["en","fr",""]:
            lang = input(f"\n{Color.Blue}🌐 Choose your language [en/fr] (current: {language}):{Color.NC} ")
            if lang.lower() not in ["en","fr",""]:
                print(f"{Color.Red}🌐 Invalid language.{Color.NC}")
        if lang != "":
            config.global_config["bot"]["default_language"] = lang.lower()

        # Prefix

        prefix = config.global_config["bot"]["default_prefix"]
        choice = input(f"\n{Color.Blue}⚜️ Choose the bot command prefix? (current: {prefix}):{Color.NC} ")
        if choice != "":
            config.global_config["bot"]["default_prefix"] = choice

        # Admins

        error = True
        while error:
            choice = input(f"\n{Color.Blue}👑 Bot admins (User ID separated with comma. Let empty to ignore):{Color.NC} ")
            if choice == "":
                error = False
                break
            admins = choice.replace(" ","").split(",")
            try:
                for admin in admins:
                    admin = int(admin)
                error = False
            except:
                print(f"{Color.Red}👑 Invalid entry. Only user ID (integers), comma and space are expected.{Color.NC}")
        if choice != "": 
            config.global_config["bot"]["admins"] = admins

        # Error channel

        error = True
        while error:
            choice = input(f"\n{Color.Blue}🤕 Error channel (Channel ID. Let empty to ignore):{Color.NC} ")
            if choice == "":
                error = False
                break
            try:
                channel = int(choice)
            except:
                print(f"{Color.Red}👑 Invalid entry. Only channel ID (integers) are expected.{Color.NC}")
        if choice != "":
            config.global_config["bot"]["error_channel"] = channel

    # End optional settings

    plugin_setup()

    # Save config

    with open("config.yaml", "w+") as conf_file:
        yaml.dump(config.global_config, conf_file)

    print(f"\n{Color.Green}✅ Setup complete!{Color.NC}")

    # Start bot

    choixe = input(f"\n▶️ Your config.py file is probably incomplete, which can break some features.\n\n{Color.Blue}▶️ Do you want to start the bot anyway? [Y/n]{Color.NC} ")
    if choixe.lower() not in decline:
        print("   Starting the bot...\n--------------------------------------------------------------------------------")
        os.system("python3 start.py")