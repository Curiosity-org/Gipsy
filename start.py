#!/usr/bin/env python
# coding=utf-8

"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""


import os
import asyncio

import discord
from LRFutils import color

from core import setup_logger

from utils import Gunibot
from core import config

import setup  # do not remove this import, it also check the dependencies pylint: disable=unused-import

if not os.path.isdir("plugins"):
    os.mkdir("plugins")

# Check and dispatch the config to all plugins

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
    Print GIPSY 1.5 ascii art
    """
    # Disable some pylints warning violations in this function
    # pylint: disable=anomalous-backslash-in-string
    # pylint: disable=trailing-whitespace
    print(
        f"""{color.fg.blue}
   _____ _____ _____   _______     __  __   _____ 
  / ____|_   _|  __ \ / ____\ \   / / /_ | | ____|
 | |  __  | | | |__) | (___  \ \_/ /   | | | |__  
 | | |_ | | | |  ___/ \___ \  \   /    | | |___ \ 
 | |__| |_| |_| |     ____) |  | |     | |_ ___) |
  \_____|_____|_|    |_____/   |_|     |_(_)____/ 
                                                  
        {color.stop}"""
    )


# ---------------#
#    M A I N    #
# ---------------#
def main():
    """
    Main function
    """

    setup_logger("discord")

    # Creating client
    client = Gunibot(
        case_insensitive=True,
        status=discord.Status.do_not_disturb,
        beta=False,
    )

    # Writing client.log + welcome message
    if not os.path.isdir("client.log"):
        os.makedirs("client.log")

    print(" ")
    client.log.info("▶️ Starting Gipsy...")

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
            except Exception as exc:  # pylint: disable=broad-except
                client.log.error(
                    "Failed to load extension: %s",
                    extension,
                    exc_info=exc,
                )
                notloaded += "\n - " + extension
                failed += 1
        return loaded, failed

    # Printing info when the bot is started
    async def on_ready():
        """Called when the bot is connected to Discord API"""
        client.log.info("%s✅ Bot connected", color.fg.green)
        client.log.info("Nom : %s", client.user.name)
        client.log.info("ID : %i", client.user.id)
        if len(client.guilds) < 200:
            servers = [x.name for x in client.guilds]
            client.log.info(
                "Connected on %i server:\n - %s",
                len(client.guilds),
                "\n - ".join(servers),
            )
        else:
            client.log.info("Connected on %i server", len(client.guilds))
        loaded, failed = await load(client, global_systems, plugins)
        client.log.info(
            "%i plugins loaded, %i plugins failed",
            loaded,
            failed,
        )

        # Syncing slash commands
        client.log.info("♻️ Syncing app commands...")
        try:
            await client.tree.sync()
        except discord.DiscordException as e:
            client.log.error("⚠️ Error while syncing app commands: %s", repr(e))
        else:
            client.log.info("✅ App commands synced")

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

    # Launch bot
    try:
        client.run(
            config.get("bot.token"),
            log_handler=None,
        )
    except discord.errors.LoginFailure:
        client.log.error("⚠️ Invalid token")
        config.token_set(force_set=True)
        os.system("python3 start.py")
        exit()


if __name__ == "__main__":
    main()
