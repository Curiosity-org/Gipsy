import discord
from discord.ext import commands

class Alakon(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "alakon"

    # Commande /cookie
    @commands.command(name="cookie")
    async def cookie(self, ctx: commands.Context, *, user: discord.User = None):
        """La fonction la plus complexe du bot: donne un cookie à l'utilisateur qui en demande."""
        if user:
            await ctx.send(f"Voilà pour vous {user.mention}: :cookie:")
        else:
            await ctx.send(f"Voilà pour vous {ctx.author.mention}: :cookie: TEST")


def setup(bot):
    bot.add_cog(Alakon(bot))
