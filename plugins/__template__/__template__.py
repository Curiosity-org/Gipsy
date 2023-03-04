"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

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
        await ctx.send(await self.bot._(ctx.guild.id, "template.hello"))
