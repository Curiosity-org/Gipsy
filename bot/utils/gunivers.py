import discord
from discord.ext import tasks, commands
from utils import Gunibot, MyContext


class Gunivers(commands.Cog):

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "gunivers"
        self.update_loop.start()

    def cog_unload(self):
        self.update_loop.cancel()

    @tasks.loop(minutes=60.0 * 24.0)
    async def update_loop(self):
        channel = self.bot.get_channel(757879277776535664) # Round Table
        if channel is not None:
            await channel.send("Bon, qu'est-ce qu'on peut poster aujourd'hui ?")

def setup(bot):
    bot.add_cog(Gunivers(bot))
