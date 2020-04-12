import discord
from discord.ext import commands
import checks


class Template(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "template"


def setup(bot):
    bot.add_cog(Template(bot))
