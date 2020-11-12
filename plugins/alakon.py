import discord
from discord.ext import commands

class Alakon(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "alakon"

    # Commande /cookie
    @commands.command(name="cookie")
    async def cookie(self, ctx):
        """La fonction la plus complexe du bot: donne un cookie à l'utilisateur qui en demande."""
        message = f"Voilà pour vous {ctx.author}: :cookie:"
        await ctx.send(message)

def setup(bot):
    bot.add_cog(Alakon(bot))
