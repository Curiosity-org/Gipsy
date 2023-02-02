#!/usr/bin/env python
# coding=utf-8

import sys
import os
import pkg_resources
import subprocess

accept = ["y", "yes", "yep", "yeah"]
decline = ["n", "no", "nope", "nah"]

# Colors:
BLUE = "\a033[34m"
GREEN = "\a033[32m"
RED = "\a033[31m"
YELLOW = "\a033[33m"
BLACK = "\a033[30m"
RESET = "\a033[0m"
ON_RED = "\a033[41m"
ON_LIGHTGRAY = "\a033[47m"



# ----------------------------------------------------------------------------------------------------
# check python version

py_version = sys.version_info
if py_version.major != 3 or py_version.minor < 10:
    print(f"⚠️ {YELLOW}Gipsy require Python 3.10 or more.\033[1m")
    sys.exit(1)



# ----------------------------------------------------------------------------------------------------
# Detect virtual environment


def get_base_prefix_compat():
    """Get base/real prefix, or sys.prefix if there is none."""
    return (
        getattr(sys, "base_prefix", None)
        or getattr(sys, "real_prefix", None)
        or sys.prefix
    )


def virtualenv() -> bool:
    """Check if the bot is running in a virtual environment."""
    return get_base_prefix_compat() != sys.prefix



# ----------------------------------------------------------------------------------------------------
# Check modules


def libs(verbose:bool = False) -> bool:
    """Check if the required libraries are installed"""
    with open("requirements.txt", "r") as file:
        packages = pkg_resources.parse_requirements(file.readlines())
    try:
        pkg_resources.working_set.resolve(packages)
    except pkg_resources.VersionConflict as e:
        if verbose:
            print(f"\n🤕 {RED}Oops, there is a problem in the dependencies.{RESET}")
            print(f"\n⚠️ {YELLOW}{type(e).__name__}: {e}{RESET}\n ")
        return False
    except Exception as e:
        if verbose:
            print(f"\n🤕 {RED}Oops, there is a problem in the dependencies.{RESET}")
            print(
                f"\n⛔ \u001b[41m\u001b[37;1m{type(e).__name__}{RESET}: {RED}{e}{RESET}"
            )
        return False
    return True



# ----------------------------------------------------------------------------------------------------
# Check plugins

def plugins(verbose:bool = False) -> bool:
    """Check if there is at least one plugin installed"""
    if not os.path.isdir("plugins"):
        return False
    for item in os.listdir("plugins"):
        if os.path.isfile(os.path.join("plugins", item, item + ".py")):
            return True
    return False



# ----------------------------------------------------------------------------------------------------
# Setup virtual environment


def setup_venv():
    choice = input(
        f"{BLUE}\n🏗️ Do you want to create a virtual environment? [Y/n]{RESET}"
    )
    if choice.lower() not in decline:
        print("Creating virtual environment...")
        os.system("python3 -m venv venv")
        print("Done!")
        print(
            f"\n🔄️ {BLUE}Please activate the virtual environment using the command below that correspond to your system. Then restart the setup script.{RESET}\n"
        )
        print(
            f"{GREEN}  Linux or MacOS (bash shell)\t:{RESET} source venv/bin/activate"
        )
        print(
            f"{GREEN}  Linux or MacOS (fish shell)\t:{RESET} source venv/bin/activate.fish"
        )
        print(
            f"{GREEN}  Linux or MacOS (csh shell)\t:{RESET} source venv/bin/activate.csh"
        )
        print(f"{GREEN}  Windows (in cmd.exe)\t\t:{RESET} venv\\Scripts\\activate.bat")
        print(f"{GREEN}  Windows (in PowerShell)\t:{RESET} venv\\Scripts\\Activate.ps1")
        print(
            '      ⮩ If you have an error like "cannot run script", you may open a new Powershell in administrator mode and run the following command: Set-ExecutionPolicy RemoteSigned\n'
        )
        exit(0)
    else:
        print("   Ok, let's stay on global environment.")
        return False



# ----------------------------------------------------------------------------------------------------
# Install dependancies


def install_dependencies():
    """Install all dependencies needed for the bot to work."""
    choice = input(
        f"{BLUE}\n🏗️ Do you want to install dependencies on the actual environment? [y/N]{RESET}"
    )
    if choice.lower() in accept:
        print("🏗️ Installing dependencies...")
        os.system("python3 -m pip install -r requirements.txt")
        print("Done!")
        return True
    else:
        print("   Dependencies not installed.")
        return False



# ----------------------------------------------------------------------------------------------------
# Ensure that the bot will run with all it's dependencies

def ensure(verbose:bool = False) -> bool:
    if not libs(verbose=verbose):
        print(
            f"\n🏗️ You need to install the bot dependencies. The automatic script will probably upgrade (or rarely downgrade) some python modules already installed on your machine."
        )
        if not virtualenv():
            setup_venv()
        if install_dependencies():
            os.system("Restarting...")
            os.system("python3 setup.py")
        else:
            print(
                f"\n⚠️ {YELLOW}The bot can't run without it's dependencies. Please install all the required modules with the following command:\033[1m\n"
            )
            print(
                f"      {BLACK}{ON_LIGHTGRAY}python3 -m pip install -r requirements.txt{RESET}\n "
            )
            exit(1)