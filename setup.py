#!/usr/bin/env python
# coding=utf-8
import os
import shutil
import subprocess
from tkinter import N
from LRFutils.color import Color
from LRFutils import log
from core import config
import sys
import yaml
import importlib
import asyncio

accept = ["y", "yes", "yep", "yeah"]
decline = ["n", "no", "nope", "nah"]
            
if __name__ == "__main__":

    config.reload_config()

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

    config.token_set()

    # Optional settings

    choice = input(f"\n{Color.Blue}Do you want to configure optional bot settings? [Y/n]:{Color.NC} ")
    if choice.lower() not in decline:
        config.advanced_setup()

    # End optional settings

    config.setup_plugins()

    asyncio.run(config.dispatch())

    # Save config

    config.save()

    print(f"\n{Color.Green}✅ Setup complete!{Color.NC}")

    # Start bot

    choice = input(f"\n▶️ Your config.py file is probably incomplete, which can break some features.\n\n{Color.Blue}▶️ Do you want to start the bot anyway? [Y/n]{Color.NC} ")
    if choice.lower() not in decline:
        print("   Starting the bot...\n--------------------------------------------------------------------------------")
        subprocess.run([sys.executable, 'start.py'])