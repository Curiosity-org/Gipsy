#!/usr/bin/env python
# coding=utf-8

# Import built-in libs
import sys
import os
import subprocess

# Ensure that the bot have all it's dependencies
from core import check_requirements
check_requirements.ensure()

# Import other modules that needs external libs
from LRFutils import color
from core import config

accept = ["y", "yes", "yep", "yeah"]
decline = ["n", "no", "nope", "nah"]



# ----------------------------------------------------------------------------------------------------
# Install plugins

def install_plugins():
    """Install plugins"""
    if not os.path.isdir("plugins"):
        os.mkdir("plugins")
    print(f"{color.Yellow}You have no plugin installed. You may consider to install plugins in order to have features on your bot.{color.NC}")    
    print(f"Here is a list of all official plugins: {color.Blue}https://github.com/Gunivers/Gipsy-plugins{color.NC}")

if __name__ == "__main__":

    if not check_requirements.plugins():
        import setup
        setup.install_plugins()

    config.token_set()

    # Optional settings
    choice = input(
        f"\n{color.Blue}Do you want to configure optional bot settings? [Y/n]:{color.NC} "
    )
    if choice.lower() not in decline:
        config.advanced_setup()

    # End optional settings
    config.setup_plugins()
    print(f"\n{color.Green}✅ Setup complete!{color.NC}")

    # Start bot
    print(
        f"\n{color.Yellow}⚠️ Before starting the bot, you should open the config.yaml file and check that everything is correct.{color.NC} "
    )
    choice = input(f"{color.Blue}▶️ Do you want to start the bot? [Y/n]{color.NC} ")
    if choice.lower() not in decline:
        print(
            "   Starting the bot...\n--------------------------------------------------------------------------------"
        )
        subprocess.run([sys.executable, "start.py"])
