import random
from datetime import datetime

import discord
from discord.ext import commands
from utils import Gunibot, MyContext


class Misc(commands.Cog):

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "misc"

    #------------------#
    # Commande /cookie #
    #------------------#

    @commands.command(name="cookie")
    @commands.guild_only()
    async def cookie(self, ctx: MyContext, *, user: discord.User = None):
        """The most usefull command: give a cookie to yourself or someone else."""
        if user:
            message = await self.bot._(ctx.guild.id, 'misc.cookie.give', to=user.mention, giver=ctx.author.mention)
        else:
            message = await self.bot._(ctx.guild.id, 'misc.cookie.self', to=ctx.author.mention)

        # Créer un webhook qui prend l'apparence d'un Villageois
        webhook: discord.Webhook = await ctx.channel.create_webhook(name=f"Villager #{random.randint(1, 9)}")
        await webhook.send(content=message, avatar_url="https://d31sxl6qgne2yj.cloudfront.net/wordpress/wp-content/uploads/20190121140737/Minecraft-Villager-Head.jpg")
        await webhook.delete()
        await ctx.message.delete()

    #------------------#
    # Commande /hoster #
    #------------------#

    @commands.command(name="hoster")
    @commands.guild_only()
    async def cookie(self, ctx: MyContext):
        """Give all informations about the hoster"""
        message = await self.bot._(ctx.guild.id, 'misc.hoster.info')

        # Créer un webhook qui prend l'apparence d'Inovaperf
        webhook: discord.Webhook = await ctx.channel.create_webhook(name="Inovaperf")
        await webhook.send(content=message, avatar_url="https://cdn.discordapp.com/icons/444578412829343754/8af3e47e5627b2c0f0eafb84c86b85b2.png")
        await webhook.delete()
        await ctx.message.delete()

    #---------------------#
    # Commande /flipacoin #
    #---------------------#

    @commands.command(name="flipacoin", aliases=['fc'])
    async def flip(self, ctx: MyContext):
        """Flip a coin."""
        a = random.randint(-100, 100)
        if a > 0:
            await ctx.send(await self.bot._(ctx.guild.id, 'misc.flipacoin.tails'))
        elif a < 0:
            await ctx.send(await self.bot._(ctx.guild.id, 'misc.flipacoin.heads'))
        else:
            await ctx.send(await self.bot._(ctx.guild.id, 'misc.flipacoin.side'))

    #------------------#
    # Commande /dataja #
    #------------------#

    @commands.command(name="dataja")
    async def dataja(self, ctx: MyContext):
        """Don't ask to ask, just ask."""
        await ctx.send(await self.bot._(ctx.guild.id, 'misc.dataja'))

    #------------------#
    # Commande /ban #
    #------------------#

    @commands.command(name="ban")
    @commands.guild_only()
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, ctx: MyContext, *, user: discord.User):
        if user == ctx.author:
            await ctx.send("Tu ne peux pas te bannir toi-même !")
            return
        if not ctx.guild.me.guild_permissions.ban_members:
            await ctx.send("Permission 'Bannir des membres' manquante :confused:")
            return
        member = ctx.guild.get_member(user.id)
        if member is not None and member.roles[-1].position >= ctx.guild.me.roles[-1].position:
            await ctx.send("Mon rôle n'est pas assez haut pour bannir cet individu :confused:")
            return
        if ctx.author.id == 125722240896598016 and random.random() > 0.7:
            kubby: discord.Member = ctx.guild.get_member(126005283704143872)
            if kubby is not None and kubby.roles[-1].position < ctx.guild.me.roles[-1].position:
                joined = kubby.joined_at.year
                curr = datetime.now().year
                invites = list()
                if ctx.guild.me.guild_permissions.manage_guild:
                    invites = await ctx.guild.invites()
                    invites = [x for x in invites if x.max_uses>1]
                elif ctx.channel.permissions_for(ctx.guild.me).create_instant_invite:
                    invites = [await ctx.channel.create_invite(max_uses=1)]
                if len(invites) > 0:
                    await kubby.send(f"Il est très probable que tu ai été banni du serveur {ctx.guild.name}. Dans le doute, voilà une invite : {invites[0].url}")
                else:
                    await kubby.send(f"Il est très probable que tu ai été banni du serveur {ctx.guild.name}. Malheureusement pour toi, je n'ai pas pu te trouver d'invitation de secours :/")
                try:
                    await ctx.guild.ban(kubby, delete_message_days=0, reason=f"Banned by {ctx.author} ({ctx.author.id})")
                except:
                    return
                await ctx.send(f"RIP kubby - {joined}-{curr}")
                return
        elif ctx.author.id != 125722240896598016:
            try:
                await ctx.guild.ban(user, delete_message_days=0, reason=f"Banned by {ctx.author} ({ctx.author.id})")
            except discord.Forbidden:
                await ctx.send("Permissions manquantes :confused: (vérifiez la hiérarchie)")
            else:
                await ctx.send(f"{user} a bien été banni !")
            return
        await ctx.send("https://thumbs.gfycat.com/LikelyColdBasil-small.gif")


    #------------------#
    # Commande /kill #
    #------------------#

    @commands.command(name="kill")
    async def kill(self, ctx: MyContext, *, target: str=None):
        """Wanna kill someone?"""
        if target is None: # victim is user
            victime = ctx.author.display_name
            ex = ctx.author.display_name.replace(" ","\_")
        else: # victim is target
            victime = target
            ex = target.replace(" ","\_")
        author = ctx.author.mention
        tries = 0
        # now let's find a random answer
        msg = 'misc.kills'
        while msg.startswith('misc.kills') or ('{0}' in msg and target is None and tries<50):
            choice = random.randint(0, 23)
            msg = await self.bot._(ctx.channel, f"misc.kills.{choice}")
            tries += 1
        # and send it
        await ctx.send(msg.format(author, victime, ex), allowed_mentions=discord.AllowedMentions.none())


# The end.
def setup(bot):
    bot.add_cog(Misc(bot))
