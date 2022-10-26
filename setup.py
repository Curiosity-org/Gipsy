#!/usr/bin/env python
# coding=utf-8
import os
import subprocess
from LRFutils import color
from core import config
import sys

accept = ["y", "yes", "yep", "yeah"]
decline = ["n", "no", "nope", "nah"]

########################
# INSTALL DEPENDENCIEs #
########################

# To remove (deprecated since added virtual environment)
def install_dependencies():
    """Install all dependencies needed for the bot to work."""
    return
    # choice = input(f"\n🏗️ You need to install the bot dependencies. The automatic script will probably upgrade (or rarely downgrade) some python modules already installed on your machine.\n{color.Blue}\n🏗️ Do you want to install dependencies? [Y/n]{color.NC}")
    # if choice.lower() in accept:
    #     print("🏗️ Installing dependencies...")
    #     os.system("pipenv install -r requirements.txt")
    # else:
    #     print("   Dependencies not installed.")
            
if __name__ == "__main__":

    if not os.path.isdir("plugins"):
        os.mkdir("plugins")

    install_dependencies()

    config.token_set()

    # Optional settings

    choice = input(f"\n{color.Blue}Do you want to configure optional bot settings? [Y/n]:{color.NC} ")
    if choice.lower() not in decline:
        config.advanced_setup()

    # End optional settings

    config.setup_plugins()

    print(f"\n{color.Green}✅ Setup complete!{color.NC}")

    # Start bot

    print(f"\n{color.Yellow}⚠️ Before starting the bot, you should open the config.yaml file and check that everything is correct.{color.NC} ")
    choice = input(f"{color.Blue}▶️ Do you want to start the bot? [Y/n]{color.NC} ")
    if choice.lower() not in decline:
        print("   Starting the bot...\n--------------------------------------------------------------------------------")
        subprocess.run([sys.executable, 'start.py'])