import discord
from discord.ext import tasks, commands
from utils import Gunibot, MyContext


class Template(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "template"

    @commands.command(name="hello")
    @commands.guild_only()
    async def hello(self, ctx: MyContext):
        await ctx.send(self.bot._(ctx.guild.id, "template.hello"))


async def setup(bot):
    await bot.add_cog(Template(bot))
