import discord
from discord.ext import commands
from utils import Gunibot


class Template(commands.Cog):

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "template"


def setup(bot):
    bot.add_cog(Template(bot))
