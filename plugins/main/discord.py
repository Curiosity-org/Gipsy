from discord.ext import commands
from core.bot import client
from core.context import MyContext

def setup(client): client.add_cog(Main())

class Main(commands.Cog):
    def __init__(self):
        self.bot = client

    @commands.group(name="config", aliases=["conf"])
    @commands.guild_only()
    @commands.cooldown(2, 15, commands.BucketType.channel)
    async def config(self, ctx: MyContext):
        """Display information about the config command."""
        await ctx.send("Hello, I'm a config")

    
    
