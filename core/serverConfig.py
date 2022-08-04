import os, json, discord, config
from discord.ext import commands

################################################################################
# Bot class definition
################################################################################

class ServerConfig():
    """
    Servers configuration.
    It only store a dictionnary containing all server configs,
    and methods that allow to manipulate this dictionnary.
    """

    all = {}

    def get(guild = None, config=None):
        """Get the server config"""

        if guild is None:
            return ServerConfig.all
        if type(guild) is discord.Guild: guild = guild.id
        if type(guild) is not str: guild = str(guild)
        if config == None:
            return ServerConfig.all[guild]
        else:
            return ServerConfig.all[guild][config]

    def update(guild_config):
        """Update the server config"""

        ServerConfig.all.update(guild_config)
        for guild, config in ServerConfig.all.items():
            if not os.path.isdir(f"data/{guild}"): os.makedirs(f"data/{guild}")
            json.dump(config, open(f"data/{guild}/server_config.json", "w"))

    def load(guilds):
        """Load the server config from files. Called when the bot is ready."""

        # Config from files
        for item in os.listdir("data"):
            if os.path.isdir(item):
                if os.path.isfile(f"data/{item}/server_config.json"):
                    ServerConfig.update({item: json.load(open("data/server_configs.json"))})
        
        # Using default config for new guilds
        for guild in guilds:
            if str(guild.id) not in ServerConfig.all:
                ServerConfig.update({str(guild.id):{
                                        "prefix": config.default_prefix,
                                        "language": config.default_language
                                    }})

    async def get_prefix(client, msg):
        """Get a prefix from a message... what did you expect?"""

        try: prefix = ServerConfig.all[msg.guild.id]["prefix"]
        except: prefix = config.default_prefix

        return commands.when_mentioned_or(prefix)(client, msg)