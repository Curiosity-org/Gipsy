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

        # Le membre donne un cookie à quelqu'un d'autre où à lui-même ?
        if user:
            message = f"Voilà pour vous {user.mention}: :cookie:\nDe la part de {ctx.author.mention}"
        else:
            message = f"Voilà pour vous {ctx.author.mention} :cookie:"

        # Créer un webhook à l'image d'un PNJ, avec un numéro random
        webhook = await ctx.channel.create_webhook(name=f"Villager #{random.randint(1, 9)}")
        await webhook.send(content=message, avatar_url="https://d31sxl6qgne2yj.cloudfront.net/wordpress/wp-content/uploads/20190121140737/Minecraft-Villager-Head.jpg")

        # Supprime le message originel ainsi que le webhook
        await webhook.delete()
        await ctx.message.delete()



    # Commande /imitate
    @commands.command(name="imitate")
    async def imitate(self, ctx: commands.Context, user: discord.User = None, *, text=None):
        """Permet de dire quelque chose sous l'apparence de quelqu'un d'autre"""

        if user and text:
            # Créer un webhook à l'image du membre ciblé
            webhook = await ctx.channel.create_webhook(name=user.name)
            await webhook.send(content=text, avatar_url=user.avatar_url)

            # Supprime le message originel ainsi que le webhook
            await webhook.delete()
            await ctx.message.delete()



    @commands.command(name="dataja")
    async def dataja(self, ctx: commands.Context):
        ctx.send("https://zrunner.me/d-a-t-a/fr.html")


def setup(bot):
    bot.add_cog(Alakon(bot))
