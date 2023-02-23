#!/usr/bin/env python
# coding=utf-8

"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import setup  # do not remove this import, it also check the dependencies

import os
import asyncio
from utils import Gunibot
import argparse
import discord
from LRFutils import color
from LRFutils import logs

if not os.path.isdir("plugins"):
    os.mkdir("plugins")

# Check and dispatch the config to all plugins
from core import config

config.check()

# Getting global system list
global_systems = []
for system in os.listdir("./bot/utils/"):
    if os.path.isfile("./bot/utils/" + system) and system[-3:] == ".py":
        global_systems.append("bot.utils." + system[0:-3])

# Getting plugin list
plugins = []
for plugin in os.listdir("./plugins/"):
    if plugin[0] not in ["_", "."]:
        if os.path.isdir("./plugins/" + plugin):
            plugins.append(f"plugins.{plugin}.{plugin}")


def print_ascii_art():
    """
    Print GIPSY 2.0 ascii art
    """
    # Disable some pylints warning violations in this function
    # pylint: disable=anomalous-backslash-in-string
    # pylint: disable=trailing-whitespace
    print(
        f"""{color.fg.blue}
      ___  ____  ____  ___  _  _        ___     ___
     / __)(_  _)(  _ \/ __)( \/ )      (__ \   / _ \\
    ( (_-. _)(_  )___/\__ \ \  /        / _/  ( (_) )
     \___/(____)(__)  (___/ (__)       (____)()\___/

        {color.stop}"""
    )


# ---------------#
#    M A I N    #
# ---------------#
def main():
    """
    Main function
    """

    # Creating client
    client = Gunibot(
        case_insensitive=True, status=discord.Status.do_not_disturb, beta=False
    )

    # Writing logs + welcome message
    if not os.path.isdir("logs"):
        os.makedirs("logs")

    print(" ")
    logs.info("▶️ Starting Gipsy...")

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
            except Exception:  # pylint: disable=broad-except
                logs.error(f"Failed to load extension: {extension}")
                notloaded += "\n - " + extension
                failed += 1
        return loaded, failed

    # Printing info when the bot is started
    async def on_ready():
        """Called when the bot is connected to Discord API"""
        logs.info(f"{color.fg.green}✅ Bot connected")
        logs.info("Nom : " + client.user.name)
        logs.info("ID : " + str(client.user.id))
        if len(client.guilds) < 200:
            serveurs = [x.name for x in client.guilds]
            logs.info(
                "Connected on "
                + str(len(client.guilds))
                + " servers:\n - "
                + "\n - ".join(serveurs)
            )
        else:
            logs.info("Connected on " + str(len(client.guilds)) + " servers")
        loaded, failed = await load(client, global_systems, plugins)
        logs.info(f"{loaded} plugins loaded, {failed} plugins failed")
        print(
            "--------------------------------------------------------------------------------"
        )
        await client.change_presence(
            status=discord.Status.online,
        )
        await asyncio.sleep(2)

        # only load plugins once
        client.remove_listener(on_ready)

    client.add_listener(on_ready)

    # Check if the bot must run in beta
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-b", "--beta", help="Run with the beta bot token", action="store_true"
    )
    args = parser.parse_args()

    # Launch bot
    try:
        client.run(config.get("bot.token"))
    except discord.errors.LoginFailure:
        logs.error("⚠️ Invalid token")
        config.token_set(force_set=True)
        os.system("python3 start.py")
        exit()


if __name__ == "__main__":
    main()
