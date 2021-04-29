#!/usr/bin/env python
# coding=utf-8

import discord
import time
import asyncio
import logging
import json
import sys
import sqlite3
from discord.ext import commands
from utils import Gunibot, setup_logger

initial_extensions = ["admin", "timeclass", "antikikoo", "contact", "errors", "general", "sconfig", "configManager", "voices", "logs", "perms", "welcome", "thanks", "groupRoles", "misc", "messageManager", "giveaways", "languages", "hypesquad", "xp", "rss", "groups"]


def main():
    with open('config.json') as f:
        conf = json.load(f)
    client = Gunibot(case_insensitive=True, status=discord.Status(
        "online"), beta=False, config=conf)
    log = setup_logger()
    log.setLevel(logging.DEBUG)
    log.info("Lancement du bot")

    # Here we load our extensions(cogs) listed above in [initial_extensions]
    count = 0
    for extension in initial_extensions:
        try:
            client.load_extension("plugins."+extension)
        except:
            log.exception(f'\nFailed to load extension {extension}')
            count += 1
        if count > 0:
            raise Exception("\n{} modules not loaded".format(count))
    del count

    async def on_ready():
        """Called when the bot is connected to Discord API"""
        print('\nBot connecté')
        print("Nom : "+client.user.name)
        print("ID : "+str(client.user.id))
        if len(client.guilds) < 200:
            serveurs = [x.name for x in client.guilds]
            print(
                "Connecté sur ["+str(len(client.guilds))+"] "+", ".join(serveurs))
        else:
            print("Connecté sur "+str(len(client.guilds))+" serveurs")
        print(time.strftime("%d/%m  %H:%M:%S"))
        print('------')
        await asyncio.sleep(2)

    client.add_listener(on_ready)

    if (not len(sys.argv) < 2):
        if (sys.argv[1].lower() == "stable"):
            client.run(conf["token"])
        elif (sys.argv[1].lower() == "beta"):
            client.beta = True
            client.run(conf["token_beta"])
    else:
        log.debug("Pas d'arguments trouvés!")
        instance_type = input("Lancer la version stable ? (y/n) ").lower()
        if instance_type == "y":
            client.run(conf["token"])
        elif instance_type == 'n':
            client.beta = True
            client.run(conf["token_beta"])


if __name__ == "__main__":
    main()
