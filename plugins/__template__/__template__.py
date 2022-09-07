import discord
from discord.ext import tasks, commands
from utils import Gunibot, MyContext

config = {}
async def setup(bot:Gunibot=None, plugin_config:dict=None):
    if bot is not None:
        await bot.add_cog(Template(bot))
    if plugin_config is not None:
        global config
        config.update(plugin_config)
    
class Template(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "template"

    @commands.command(name="hello")
    @commands.guild_only()
    async def hello(self, ctx: MyContext):
        await ctx.send(self.bot._(ctx.guild.id, "template.hello"))
