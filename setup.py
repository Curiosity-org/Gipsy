#!/usr/bin/env python
# coding=utf-8

import sys
import os
import pkg_resources
import subprocess

accept = ["y", "yes", "yep", "yeah"]
decline = ["n", "no", "nope", "nah"]

# ________________________________________________________________________________
# check python version

py_version = sys.version_info
if py_version.major != 3 or py_version.minor < 9:
    print("⚠️ \033[33mGipsy require Python 3.10 or more.\033[1m")
    sys.exit(1)

# ________________________________________________________________________________
# Detect virtual environment

def get_base_prefix_compat():
    """Get base/real prefix, or sys.prefix if there is none."""
    return getattr(sys, "base_prefix", None) or getattr(sys, "real_prefix", None) or sys.prefix

def in_virtualenv():
    return get_base_prefix_compat() != sys.prefix

# ________________________________________________________________________________
# Check modules

def check_libs(verbose=False):
    """Check if the required libraries are installed and can be imported"""
    with open("requirements.txt", 'r') as file:
        packages = pkg_resources.parse_requirements(file.readlines())
    try:
        pkg_resources.working_set.resolve(packages)
    except pkg_resources.VersionConflict as e:
        if verbose:
            print(f"\n🤕 \033[31mOops, there is a problem in the dependencies.\033[0m")
            print(f"\n⚠️ \033[33m{type(e).__name__}: {e}\033[0m\n ")
        return False
    except Exception as e:
        if verbose:
            print(f"\n🤕 \033[31mOops, there is a problem in the dependencies.\033[0m")
            print(f"\n⛔ \u001b[41m\u001b[37;1m{type(e).__name__}\033[0m: \033[31m{e}\033[0m")
        return False
    return True

# ________________________________________________________________________________
# Setup virtual environment

def setup_venv():
    choice = input(f"\033[34m\n🏗️ Do you want to create a virtual environment? [Y/n]\033[0m")
    if choice.lower() not in decline:
        print("Creating virtual environment...")
        os.system("python3 -m venv venv")
        print("Done!")
        print("\n🔄️ \033[34mPlease activate the virtual environment using the command below that correspond to your system. Then restart the setup script.\033[0m\n")
        print("\033[32m  Linux or MacOS (bash shell)\t:\033[0m source venv/bin/activate")
        print("\033[32m  Linux or MacOS (fish shell)\t:\033[0m source venv/bin/activate.fish")
        print("\033[32m  Linux or MacOS (csh shell)\t:\033[0m source venv/bin/activate.csh")
        print("\033[32m  Windows (in cmd.exe)\t\t:\033[0m venv\\Scripts\\activate.bat")
        print("\033[32m  Windows (in PowerShell)\t:\033[0m venv\\Scripts\\Activate.ps1")
        print("      ⮩ If you have an error like \"cannot run script\", you may open a new Powershell in administrator mode and run the following command: Set-ExecutionPolicy RemoteSigned\n")
        exit(0)
    else:
        print("   Ok, let's stay on global environment.")
        return False

# ________________________________________________________________________________
# Install dependancies

def install_dependencies():
    """Install all dependencies needed for the bot to work."""
    choice = input(f"\033[34m\n🏗️ Do you want to install dependencies on the actual environment? [y/N]\033[0m")
    if choice.lower() in accept:
        print("🏗️ Installing dependencies...")
        os.system("python3 -m pip install -r requirements.txt")
        print("Done!")
        return True
    else:
        print("   Dependencies not installed.")
        return False

if __name__ == "__main__":
    verbose = False
else:
    verbose = True

if not check_libs(verbose=verbose):
    print(f"\n🏗️ You need to install the bot dependencies. The automatic script will probably upgrade (or rarely downgrade) some python modules already installed on your machine.")
    if not in_virtualenv():
        setup_venv()
    if install_dependencies():
        os.system("Restarting...")
        os.system("python3 setup.py")
    else:
        print("\n⚠️ \033[33mThe bot can't run without it's dependancies. Please install all the required modules with the following command:\033[1m\n")
        print("       \u001b[47m\033[30mpython3 -m pip install -r requirements.txt\033[0m\n ")
        exit(1)

# ________________________________________________________________________________
# Import modules

import subprocess
from LRFutils import color
from core import config
import sys

# ________________________________________________________________________________
# Setup script

if __name__ == "__main__":

    if not os.path.isdir("plugins"):
        os.mkdir("plugins")

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