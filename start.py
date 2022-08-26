#!/usr/bin/env python
# coding=utf-8
"""
Gipsy start functions
"""


import argparse
import asyncio
import logging
import os
import sys
import time
import discord

from bot.docs import generate_docs
from bot.config import get_config
from utils import Gunibot, setup_logger

# check python version
py_version = sys.version_info
if py_version.major != 3 or py_version.minor < 9:
    print("Vous devez utiliser au moins Python 3.9 !", file=sys.stderr)
    sys.exit(1)

# Getting global system list
global_systems = []
for system in os.listdir('./bot/utils/'):
    if os.path.isfile('./bot/utils/' + system) and system[-3:] == '.py':
        global_systems.append("bot.utils." + system[0:-3])

# Getting plugin list
plugins = []
for plugin in os.listdir('./plugins/'):
    if plugin[0] != '_':
        if os.path.isdir('./plugins/' + plugin):
            plugins.append("plugins." + plugin + '.bot.main')

# Generate docs
generate_docs()


def print_ascii_art():
    """
    Print GIPSY 2.0 ascii art
    """
    # Disable all the anomalous-backslash-in-string violations in this function
    # pylint: disable=anomalous-backslash-in-string
    print("""
      ___  ____  ____  ___  _  _        ___     ___  
     / __)(_  _)(  _ \/ __)( \/ )      (__ \   / _ \\ 
    ( (_-. _)(_  )___/\__ \ \  /        / _/  ( (_) )
     \___/(____)(__)  (___/ (__)       (____)()\___/ 

        """)


# ---------------#
#    M A I N    #
# ---------------#
def main():
    """
    Main function
    """
    # Getting global config
    conf = get_config('./config/config', isBotConfig=True)
    if conf is None:
        return 1

    # Getting plugins configs
    for plugin_dir in os.listdir('./plugins/'):
        if plugin_dir[0] != '_':
            if os.path.isfile('./plugins/' + plugin_dir + '/config/require-example.json'):
                conf.update(
                    get_config('./plugins/' + plugin_dir + '/config/require', isBotConfig=False)
                )

    # Creating client
    client = Gunibot(
        case_insensitive=True,
        status=discord.Status("online"),
        beta=False,
        config=conf
    )

    # Writing logs + welcome message
    if not os.path.isdir("logs"):
        os.makedirs("logs")
    log = setup_logger()
    log.setLevel(logging.DEBUG)
    log.info("Lancement du bot")

    # pylint: disable-next=anomalous-backslash-in-string
    print_ascii_art()

    # Loading extensions (global system + plugins)
    async def load(bot_client, global_system_list, plugin_list):
        loaded = 0
        failed = 0
        notloaded = ""
        for extension in global_system_list + plugin_list:
            try:
                await bot_client.load_extension(extension)
                loaded += 1
            except Exception: # pylint: disable=broad-except
                log.exception('Failed to load extension: %s', extension)
                notloaded += "\n - " + extension
                failed += 1
        if failed > 0:
            raise Exception(f"\n{failed} modules not loaded" + notloaded)
        return loaded, failed

    # Printing info when the bot is started
    async def on_ready():
        """Called when the bot is connected to Discord API"""
        print('Bot connecté')
        print("Nom : " + client.user.name)
        print("ID : " + str(client.user.id))
        if len(client.guilds) < 200:
            serveurs = [x.name for x in client.guilds]
            print(
                "Connecté sur [" + str(len(client.guilds)) + "] " + ", ".join(serveurs))
        else:
            print("Connecté sur " + str(len(client.guilds)) + " serveurs")
        print(time.strftime("%d/%m  %H:%M:%S"))
        loaded, failed = await load(client, global_systems, plugins)
        print(f"{loaded} plugins chargés, {failed} plugins en erreur")
        print('------')
        await asyncio.sleep(2)

    client.add_listener(on_ready)

    # Check if the bot must run in beta
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--beta", help="Run with the beta bot token", action='store_true')
    args = parser.parse_args()

    # Launch bot
    if args.beta:
        client.beta = True
        client.run(conf["token_beta"])
    else:
        client.run(conf["token"])


if __name__ == "__main__":
    main()
