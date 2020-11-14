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

        # Créer un webhook qui prend l'apparence d'un Villageois
        webhook = await ctx.channel.create_webhook(name=f"Villager #{random.randint(1, 9)}")
        await webhook.send(content=message, avatar_url="https://d31sxl6qgne2yj.cloudfront.net/wordpress/wp-content/uploads/20190121140737/Minecraft-Villager-Head.jpg")
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



    # Commande /dataja
    @commands.command(name="dataja")
    async def dataja(self, ctx: commands.Context):
        """Une commande incroyablement utile et riche en informations"""
        await ctx.send("https://zrunner.me/d-a-t-a/fr.html")



    # Commande /move <MessageID> <Channel>
    @commands.command(names="move")
    async def move(self, ctx: commands.Context, msg: discord.Message, channel: discord.TextChannel):
        """Permet de déplacer un message d'un salon à un autre"""
        if msg and channel:

            # Créé un webhook pour renvoyer le message dans un autre salon
            webhook = await channel.create_webhook(name=msg.author.name)
            await webhook.send(content=msg.content, avatar_url=msg.author.avatar_url)
            await webhook.delete()

            # Créé un embed pour prévenir que le message à été déplacé
            embed = discord.Embed(
                description=f"{msg.author.mention}, votre message à été déplacé dans {channel.mention}",
                colour=discord.Colour(51711)
            )
            embed.set_footer(text=f"Déplacé par {ctx.author.name}")
            await ctx.send(embed=embed)

            # Supprime la commande ainsi que le message originel
            await msg.delete()
            await ctx.message.delete()

def setup(bot):
    bot.add_cog(Alakon(bot))
