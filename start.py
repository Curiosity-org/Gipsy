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


initial_extensions = ["admin", "timeclass", "antikikoo", "contact", "errors", "general", "sconfig", "configManager", "voices", "logs", "perms", "welcome", "thanks"]


class gunibot(commands.bot.BotBase, discord.Client):

    def __init__(self, case_insensitive=None, status=None, beta=False, config: dict = None):
        self.config = config
        super().__init__(command_prefix=self.get_prefix, case_insensitive=case_insensitive,
                         status=status, allowed_mentions=discord.AllowedMentions(everyone=False, roles=False))
        self.log = logging.getLogger("runner")
        self.beta = beta
        self.database = sqlite3.connect('data/database.db')
        self._update_database_structure()

    @property
    def server_configs(self):
        return self.get_cog("ConfigCog").confManager

    def _update_database_structure(self):
        """Create tables and indexes from 'data/model.sql' file"""
        c = self.database.cursor()
        with open('data/model.sql', 'r', encoding='utf-8') as f:
            c.executescript(f.read())
        c.close()

    async def user_avatar_as(self, user, size=512):
        """Get the avatar of an user, format gif or png (as webp isn't supported by some browsers)"""
        if not hasattr(user, "avatar_url_as"):
            raise ValueError
        try:
            if user.is_avatar_animated():
                return user.avatar_url_as(format='gif', size=size)
            else:
                return user.avatar_url_as(format='png', size=size)
        except Exception as e:
            await self.cogs['ErrorsCog'].on_error(e, None)

    class SafeDict(dict):
        def __missing__(self, key):
            return '{' + key + '}'

    async def get_prefix(self, msg):
        prefix = None
        if msg.guild is not None:
            prefix = self.server_configs[msg.guild.id]["prefix"]
        if prefix is None:
            prefix = "?"
        return commands.when_mentioned_or(prefix)(self, msg)

    async def update_config(self, key: str, value):
        """Change a value in the config file
        No undo can be done"""
        self.config[key] = value
        with open("config.json", 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)


# async def get_prefix(bot, msg):
#     return commands.when_mentioned_or(bot.config.get("prefix", "?"))(bot, msg)

def setup_logger():
    # on chope le premier logger
    log = logging.getLogger("runner")
    # on défini un formatteur
    format = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s", datefmt="[%d/%m/%Y %H:%M]")
    # ex du format : [08/11/2018 14:46] WARNING RSSCog fetch_rss_flux l.288 : Cannot get the RSS flux because of the following error: (suivi du traceback)

    # log vers un fichier
    file_handler = logging.FileHandler("debug.log")
    # tous les logs de niveau DEBUG et supérieur sont evoyés dans le fichier
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(format)

    # log vers la console
    stream_handler = logging.StreamHandler(sys.stdout)
    # tous les logs de niveau INFO et supérieur sont evoyés dans le fichier
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(format)

    # supposons que tu veuille collecter les erreurs sur ton site d'analyse d'erreurs comme sentry
    #sentry_handler = x
    # sentry_handler.setLevel(logging.ERROR)  # on veut voir que les erreurs et au delà, pas en dessous
    # sentry_handler.setFormatter(format)

    # log.debug("message de debug osef")
    # log.info("message moins osef")
    # log.warn("y'a un problème")
    # log.error("y'a un gros problème")
    # log.critical("y'a un énorme problème")

    log.addHandler(file_handler)
    log.addHandler(stream_handler)
    # log.addHandler(sentry_handler)

    return log


def main():
    with open('config.json') as f:
        conf = json.load(f)
    client = gunibot(case_insensitive=True, status=discord.Status(
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
            client.run(conf["token_beta"])
    else:
        log.debug("Pas d'arguments trouvés!")
        client.run(conf["token"] if input(
        "Lancer la version stable ? (y/n) ").lower() == "y" else conf["token_beta"])


if __name__ == "__main__":
    main()
