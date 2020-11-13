import discord
import random
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
            message = f"Voilà pour vous {user.mention}: :cookie:\nDe la part de {ctx.author.mention}"
        else:
            message = f"Voilà pour vous {ctx.author.mention} :cookie:"
        webhook = await ctx.channel.create_webhook(name=f"Villager #{random.randint(1, 9)}")
        await webhook.send(content=message, avatar_url="https://d31sxl6qgne2yj.cloudfront.net/wordpress/wp-content/uploads/20190121140737/Minecraft-Villager-Head.jpg")
        await webhook.delete()
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(Alakon(bot))
