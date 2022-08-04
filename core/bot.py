import discord
from discord.ext import commands
import sqlite3
from core.context import MyContext
import config
import os
import json
import os, json, config

################################################################################
# Bot class definition
################################################################################

class Sconfig():
    all = {}

    def get(guild = None, config=None):
        """Get the server config"""
        if guild is None:
            return Sconfig.all
        if type(guild) is discord.Guild: guild = guild.id
        if type(guild) is not str: guild = str(guild)
        if config == None:
            return Sconfig.all[guild]
        else:
            return Sconfig.all[guild][config]

    def update(guild_config):
        """Update the server config"""
        Sconfig.all.update(guild_config)
        for guild, config in Sconfig.all.items():
            if not os.path.isdir(f"data/{guild}"): os.makedirs(f"data/{guild}")
            json.dump(config, open(f"data/{guild}/server_config.json", "w"))

    def load():
        for item in os.listdir("data"):
            if os.path.isdir(item):
                if os.path.isfile(f"data/{item}/server_config.json"):
                    Sconfig.update({item: json.load(open("data/server_configs.json"))})

        for guild in client.guilds:
            if str(guild.id) not in Sconfig.all:
                Sconfig.update({str(guild.id):{
                                        "prefix": config.default_prefix,
                                        "language": config.default_language
                                    }})

    async def get_prefix(client, msg):
        """Get a prefix from a message... what did you expect?"""

        try: prefix = Sconfig.all[msg.guild.id]["prefix"]
        except: prefix = config.default_prefix

        return commands.when_mentioned_or(prefix)(client, msg)

class Gipsy(commands.bot.AutoShardedBot):

    def __init__(self, status=None):
        ALLOWED = discord.AllowedMentions(everyone=False, roles=False)
        intents = discord.Intents.default()
        super().__init__(
            command_prefix=Sconfig.get_prefix,
            case_insensitive=True,
            status=status,
            allowed_mentions=ALLOWED,
            intents=intents)

    async def on_ready(self):
        Sconfig.load()

client = Gipsy(status="online")