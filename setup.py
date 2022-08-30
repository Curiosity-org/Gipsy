import os
import shutil
from tkinter import N
from LRFutils.color import Color
from LRFutils import log

accept = ["y", "yes", "yeah", "ye"]
refuse = ["n", "no", "nope", "nah"]

###############
# TOKEN CHECK #
###############

def token_set(force_set = False):
    """Check if the token is set, if not, ask for it. Return True if the token is set, False if not."""

    import config

    if config.bot.token is None or force_set:
        # Explain how to get a token
        print(f"\n🔑 You need to set your Discord bot token in config.py.\n   To do so, go on {Color.Blue}https://discord.com/developers/applications{Color.NC}, select your application, go in bot section and copy your token.\n   To create a bot application, please refere to this page: {Color.Blue}https://discord.com/developers/docs/intro{Color.NC}.\n   Also, be sure to anable all intents.\n")
        
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
            print(f"\n{Color.Green}✅ Setup complete!{Color.NC}")
    return True

#####################
# SQUASHING CONFIGS #
#####################

def squash_config():

    print("\n📦 Squashing configuration files...")

    with open("core/default_config.py", "r") as f:
        before = []
        started = False
        for line in f:
            if not started: before.append(line)
            if line.startswith("# Plugin config"): started = True

    with open("core/default_config.py","w+") as config:
        for line in before: config.write(line)
        config.write("\n")

        for plugin in os.listdir(f'plugins'):
            if os.path.isfile(f'plugins/' + plugin + "/config.py"):
                config.write(f"\n# {plugin}\n")
                for line in open(f'plugins/' + plugin + "/config.py", "r"):
                    config.write(line)

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

# Check basic requirements and start this script if something is missing
if __name__ != "__main__":
    if not os.path.isfile("config.py"):
        log.warn("⛔ The bot is not correctly setup. Running setup script...")
        os.system("python3 setup.py")
        exit()

if __name__ == "__main__":

    squash_config()  

    install_dependencies()

    if not token_set(): exit()

    #############
    # START BOT #
    #############

    choixe = input(f"\n▶️ Your config.py file is probably incomplete, which can break some features.\n\n{Color.Blue}▶️ Do you want to start the bot anyway? [Y/n]{Color.NC} ")
    if choixe.lower() not in refuse:
        print("   Starting the bot...\n--------------------------------------------------------------------------------")
        os.system("python3 start.py")