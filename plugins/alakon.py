import discord
import random
from discord.ext import commands


# Déplace un message depuis son salon d'origine vers un salon passé en paramètre, le tout en utilisant un webhook donné
async def moveMessage(msg, channel, webhook):
    files = [await x.to_file() for x in msg.attachments]
    await webhook.send(content=msg.content, files=files, embeds=msg.embeds, avatar_url=msg.author.avatar_url, username=msg.author.name)
    await msg.delete()


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
    @commands.command(names="move", aliases=['mv'])
    async def move(self, ctx: commands.Context, msg: discord.Message, channel: discord.TextChannel, *, confirm = True):
        """Permet de déplacer un message d'un salon à un autre"""

        # Créé un webhook pour renvoyer le message dans un autre salon
        webhook = await channel.create_webhook(name="Gunipy Hook")
        await moveMessage(msg, channel, webhook)
        await webhook.delete()

        if confirm:
            # Créé un embed pour prévenir que le message à été déplacé
            embed = discord.Embed(
                description=f"{msg.author.mention}, votre message à été déplacé dans {channel.mention}",
                colour=discord.Colour(51711)
            )
            embed.set_footer(text=f"Message déplacé par {ctx.author.name}")
            await ctx.send(embed=embed)

        # Supprime la commande
        await ctx.message.delete()


    # Commande /moveall <MessageID> <MessageID> <Channel>
    @commands.command(names="moveall", aliases=['mva'])
    async def moveall(self, ctx: commands.Context, msg1: discord.Message, msg2: discord.Message, channel: discord.TextChannel, *, confirm = True):
        """Permet de déplacer plusieurs messages d'un seul coup"""

        # Vérification des permissions
        perm1 = ctx.channel.permissions_for(ctx.guild.me)
        perm2 = channel.permissions_for(ctx.guild.me)

        if not (perm1.read_messages and perm1.read_message_history and perm1.manage_messages and perm2.read_messages and perm2.manage_webhooks):
            ctx.send("pas les perms >:(")
            self.bot.log.info(f"Alakon - /moveall: Missing permissions on guild \"{ctx.guild.name}\"")
            return

        # Création du webhook (commun à tous les messages)
        webhook = await channel.create_webhook(name="Gunipy Hook")

        # Vérifie que les messages sont dans le même salon
        if msg1.channel != msg2.channel:
            ctx.send("Les messages doivent être dans le même salon")
        else:

            # Fait en sorte que msg1 soit bel et bien le premier message des deux
            if msg1.created_at > msg2.created_at:
                msg = msg1
                msg1 = msg2
                msg2 = msg1

            # Récupère la liste des messages depuis msg1
            msgList = await msg1.channel.history(limit=20, after=msg1).flatten()
            if len(msgList) == 0:
                ctx.send("Aucun message trouvé")
            else:

                # Déplace successivement tous les messages de la liste jusqu'à arriver à msg2
                msg = msg1
                await moveMessage(msg, channel, webhook)

                i = 0
                msg = msgList[0]
                while msg != msg2:
                    await moveMessage(msg, channel, webhook)
                    i += 1
                    msg = msgList[i]

                msg = msg2
                await moveMessage(msg, channel, webhook)

                if confirm:
                    # Créé un embed pour prévenir que le message à été déplacé
                    embed = discord.Embed(
                        description = f"Plusieurs messages ont été déplacés dans {channel.mention}",
                        colour = discord.Colour(51711)
                    )
                    embed.set_footer(text=f"Messages déplacés par {ctx.author.name}")
                    await ctx.send(embed=embed)
                    await ctx.message.delete()

                await webhook.delete()




def setup(bot):
    bot.add_cog(Alakon(bot))
