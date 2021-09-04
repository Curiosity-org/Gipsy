import discord
from discord.ext import tasks, commands
from utils import Gunibot


class Template(commands.Cog):

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "template"

    @commands.command(name="hello")
    @commands.guild_only()
    async def hello(self, ctx: MyContext):
        await ctx.send(self.bot._(ctx.guild.id, 'template.hello'))

def setup(bot):
    bot.add_cog(Template(bot))
