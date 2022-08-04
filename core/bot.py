import discord
from discord.ext import commands
from core.serverConfig import ServerConfig

class Gipsy(commands.bot.AutoShardedBot):
    """Main bot class."""

    def __init__(self, status=None):
        ALLOWED = discord.AllowedMentions(everyone=False, roles=False)
        intents = discord.Intents.default()
        super().__init__(
            command_prefix=ServerConfig.get_prefix,
            case_insensitive=True,
            status=status,
            allowed_mentions=ALLOWED,
            intents=intents)

    async def on_ready(self):
        ServerConfig.load(self.guilds)

client = Gipsy(status="online")