#!/usr/bin/env python
# coding=utf-8

"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import sys
import os
import subprocess

import pkg_resources
from LRFutils import color

from core import config
from core.config import ask_user

# ________________________________________________________________________________
# check python version

py_version = sys.version_info
if py_version.major != 3 or py_version.minor < 10:
    print("⚠️ \033[33mGipsy require Python 3.10 or more.\033[1m")
    sys.exit(1)


# ________________________________________________________________________________
# Detect virtual environment


def get_base_prefix_compat():
    """Get base/real prefix, or sys.prefix if there is none."""
    return (
            getattr(sys, "base_prefix", None)
            or getattr(sys, "real_prefix", None)
            or sys.prefix
    )


def in_virtualenv():
    return get_base_prefix_compat() != sys.prefix


# ________________________________________________________________________________
# Check modules


def check_libs(verbose=False):
    """Check if the required libraries are installed and can be imported"""
    with open("requirements.txt", "r", encoding='utf-8') as file:
        packages = pkg_resources.parse_requirements(file.readlines())
    try:
        pkg_resources.working_set.resolve(packages)
    except pkg_resources.VersionConflict as exc:
        if verbose:
            print("\n🤕 \033[31mOops, there is a problem in the dependencies.\033[0m")
            print(f"\n⚠️ \033[33m{type(exc).__name__}: {exc}\033[0m\n ")
        return False
    except Exception as exc:  # pylint: disable=broad-exception-caught
        if verbose:
            print("\n🤕 \033[31mOops, there is a problem in the dependencies.\033[0m")
            print(
                f"\n⛔ \u001b[41m\u001b[37;1m{type(exc).__name__}\033[0m: \033[31m{exc}\033[0m"
            )
        return False
    return True


# ________________________________________________________________________________
# Setup virtual environment


def setup_venv():
    opt_venv = ask_user(
        "Do you want to create a virtual environment?",
        default=True,
        emoji="🏗️"
    )
    if opt_venv:
        print("Creating virtual environment...")
        os.system("python3 -m venv venv")
        print("Done!")
        print(
            "\n🔄️ \033[34mPlease activate the virtual environment using the command below that" \
            "correspond to your system. Then restart the setup script.\033[0m\n"
        )
        print(
            "\033[32m  Linux or MacOS (bash shell)\t:\033[0m source venv/bin/activate"
        )
        print(
            "\033[32m  Linux or MacOS (fish shell)\t:\033[0m source venv/bin/activate.fish"
        )
        print(
            "\033[32m  Linux or MacOS (csh shell)\t:\033[0m source venv/bin/activate.csh"
        )
        print("\033[32m  Windows (in cmd.exe)\t\t:\033[0m venv\\Scripts\\activate.bat")
        print("\033[32m  Windows (in PowerShell)\t:\033[0m venv\\Scripts\\Activate.ps1")
        print(
            '      ⮩ If you have an error like "cannot run script", you may open a new Powershell' \
            'in administrator mode and run the following command:' \
            'Set-ExecutionPolicy RemoteSigned\n'
        )
        exit(0)
    else:
        print("   Ok, let's stay on global environment.")
        return False


# ________________________________________________________________________________
# Install dependancies


def install_dependencies():
    """Install all dependencies needed for the bot to work."""
    opt_deps = ask_user(
        "🏗️ Do you want to install dependencies on the actual environment?"
    )
    if opt_deps:
        print("🏗️ Installing dependencies...")
        os.system("python3 -m pip install -r requirements.txt")
        print("Done!")
        return True
    else:
        print("   Dependencies not installed.")
        return False


if __name__ == "__main__":
    VERBOSE = False
else:
    VERBOSE = True

if not check_libs(verbose=VERBOSE):
    print(
        "\n🏗️ You need to install the bot dependencies. The automatic script will probably upgrade" \
        "(or rarely downgrade) some python modules already installed on your machine."
    )
    if not in_virtualenv():
        setup_venv()
    if install_dependencies():
        os.system("Restarting...")
        os.system("python3 setup.py")
    else:
        print(
            "\n⚠️ \033[33mThe bot can't run without it's dependencies. Please install" \
            "all the required modules with the following command:\033[1m\n"
        )
        print(
            "       \u001b[47m\033[30mpython3 -m pip install -r requirements.txt\033[0m\n "
        )
        exit(1)


# ________________________________________________________________________________
# Setup script

def main():
    if not os.path.isdir("plugins"):
        os.mkdir("plugins")

    config.token_set()

    # Optional settings

    opt_bot_settings = ask_user(
        "Do you want to configure optional bot settings?",
        default=False
    )
    if opt_bot_settings:
        config.advanced_setup()

    # End optional settings

    config.setup_plugins()

    print(f"\n{color.fg.green}✅ Setup complete!{color.stop}")


if __name__ == "__main__":

    main()

    # Start bot

    print(
        f"\n{color.fg.yellow}⚠️ Before starting the bot, you should open the config.yaml file" \
        f"and check that everything is correct.{color.stop} "
    )
    opt_start = ask_user(
        "Do you want to start the bot?",
        default=False,
        emoji="▶️")
    if opt_start:
        print(
            "   Starting the bot..."
        )
        print("-" * 80)
        subprocess.run([sys.executable, "start.py"])  # pylint: disable=subprocess-run-check
