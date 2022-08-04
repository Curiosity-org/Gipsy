import random

import discord.abc
import nextcord
from nextcord.ext import commands
from utils import Gunibot, MyContext


class Ban(commands.Cog):

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "ban"

    # ------------------#
    # Commande /ban    #
    # ------------------#

    @commands.command(name="ban")
    @commands.guild_only()
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, ctx: MyContext, *, user: nextcord.User, reason: str = "Aucune raison donnée"):
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
        if ctx.guild.id != 125723125685026816 and ctx.guild.id != 689159304049197131:
            try:
                await ctx.guild.ban(user, delete_message_days=0,
                                    reason=f"Banned by {ctx.author} ({ctx.author.id}). Reason : {reason}")
            except nextcord.Forbidden:
                await ctx.send("Permissions manquantes :confused: (vérifiez la hiérarchie)")
            else:
                await ctx.send(f"{user} a bien été banni !")
            await ctx.send("https://thumbs.gfycat.com/LikelyColdBasil-small.gif")
            return

            # GUNIVERS/CURIOSITY SPECIAL CASES
        else:

            # 1/10th chance of banning the command executor instead, Uno Reverse event.
            if random.randint(1, 10) == 1:
                if ctx.guild.id == 125723125685026816:
                    await ctx.author.send("https://discord.gg/E8qq6tN")
                else:
                    await ctx.author.send("https://discord.gg/jtntCqXz53")
                try:
                    await ctx.guild.kick(ctx.author,
                                         reason=f"Banned by himself. Reason : {user} ({user.id}) used Uno Reverse card.")
                except nextcord.Forbidden:
                    await ctx.send("Permissions manquantes :confused: (vérifiez la hiérarchie)")
                else:
                    # Find and send some random message
                    choice = random.randint(0, 3)
                    msg = await self.bot._(ctx.channel, f"ban.gunivers.selfban.{choice}")
                    await ctx.send(msg.format(ctx.author.mention, user.mention))
                    await ctx.send("https://thumbs.gfycat.com/BackInsignificantAfricanaugurbuzzard-size_restricted.gif")
                return

            # 1/10th chance of banning both banned and executor, Bothban event.
            if random.randint(1, 10) == 1:
                if ctx.guild.id == 125723125685026816:
                    await user.send("https://discord.gg/E8qq6tN")
                else:
                    await user.send("https://discord.gg/jtntCqXz53")
                try:
                    await ctx.guild.kick(user, reason=f"Banned by {ctx.author} ({ctx.author.id}). Reason : {reason}")
                except nextcord.Forbidden:
                    await ctx.send("Permissions manquantes :confused: (vérifiez la hiérarchie)")
                else:
                    if ctx.guild.id == 125723125685026816:
                        await ctx.author.send("https://discord.gg/E8qq6tN")
                    else:
                        await ctx.author.send("https://discord.gg/jtntCqXz53")
                    try:
                        await ctx.guild.kick(ctx.author,
                                             reason=f"Banned by himself. Reason : {user} ({user.id}) banned him back.")
                    except nextcord.Forbidden:
                        # If there's an error when banning the author, we don't care and act like if a one-way ban happened.
                        choice = random.randint(0, 9)
                        msg = await self.bot._(ctx.channel, f"ban.gunivers.ban.{choice}")
                        await ctx.send(msg.format(ctx.author.mention, user.mention))
                        await ctx.send("https://thumbs.gfycat.com/PepperyEminentIndianspinyloach-size_restricted.gif")
                    else:
                        # If there's no error, find a random message and send it.
                        choice = random.randint(0, 3)
                        msg = await self.bot._(ctx.channel, f"ban.gunivers.bothban.{choice}")
                        await ctx.send(msg.format(ctx.author.mention, user.mention))
                        await ctx.send(
                            "https://thumbs.gfycat.com/BackInsignificantAfricanaugurbuzzard-size_restricted.gif")
                return

            # 1/10th chance of rickrolling people, Rickroll event.
            if random.randint(1, 10) == 1:
                await self.bot._(ctx.channel, f"ban.gunivers.rickroll")
                await ctx.send(
                    "Never gonna give you up,\nnever gonna let you down,\nnever gonna run around and ban you :musical_note:")
                await ctx.send("https://thumbs.gfycat.com/VengefulDesertedHalibut-size_restricted.gif")
                return

            # If ban is issued by Leirof, then Bald ban event.
            if ctx.author.id == 125722240896598016:
                if ctx.guild.id == 125723125685026816:
                    await user.send("https://discord.gg/E8qq6tN")
                else:
                    await user.send("https://discord.gg/jtntCqXz53")
                try:
                    await ctx.guild.kick(user, reason=f"Banned by {ctx.author} ({ctx.author.id}). Reason : {reason}")
                except nextcord.Forbidden:
                    await ctx.send("Permissions manquantes :confused: (vérifiez la hiérarchie)")
                else:
                    # Find and send some random message
                    choice = random.randint(0, 9)
                    msg = await self.bot._(ctx.channel, f"ban.gunivers.ban.{choice}")
                    await ctx.send(msg.format(ctx.author.mention, user.mention))
                    await ctx.send("https://thumbs.gfycat.com/PepperyEminentIndianspinyloach-size_restricted.gif")
                    await ctx.send(
                        "https://media.discordapp.net/attachments/791335982666481675/979052868915064862/Chauve_qui_peut_.png")
                return

            # else, normal ban w/ random message
            else:
                if ctx.guild.id == 125723125685026816:
                    await user.send("https://discord.gg/E8qq6tN")
                else:
                    await user.send("https://discord.gg/jtntCqXz53")
                try:
                    await ctx.guild.kick(user, reason=f"Banned by {ctx.author} ({ctx.author.id}). Reason : {reason}")
                except nextcord.Forbidden:
                    await ctx.send("Permissions manquantes :confused: (vérifiez la hiérarchie)")
                else:
                    # Find and send some random message
                    choice = random.randint(0, 9)
                    msg = await self.bot._(ctx.channel, f"ban.gunivers.ban.{choice}")
                    await ctx.send(msg.format(ctx.author.mention, user.mention))
                    await ctx.send("https://thumbs.gfycat.com/PepperyEminentIndianspinyloach-size_restricted.gif")
                return

    # ------------------#
    # Commande /rban   #
    # ------------------#
    # Parce qu'il peut être pratique de bannir tout de même

    @commands.command(name="rban")
    @commands.guild_only()
    @commands.has_guild_permissions(ban_members=True)
    async def rban(self, ctx: MyContext, *, user: nextcord.User, reason: str = "Aucune raison donnée"):
        if ctx.guild.id == 125723125685026816 or ctx.guild.id == 689159304049197131:
            if user == ctx.author:
                await ctx.send("Tu ne peux pas te bannir toi-même abruti !")
                return
            if not ctx.guild.me.guild_permissions.ban_members:
                await ctx.send("Permission 'Bannir des membres' manquante, c'est con :confused:")
                return
            member = ctx.guild.get_member(user.id)
            if member is not None and member.roles[-1].position >= ctx.guild.me.roles[-1].position:
                await ctx.send("Mon rôle n'est pas assez haut pour bannir cet individu :confused:")
                return
            try:
                await ctx.guild.ban(user, delete_message_days=0,
                                    reason=f"Banned by {ctx.author} ({ctx.author.id}). Reason : {reason}")
            except nextcord.Forbidden:
                await ctx.send("Permissions manquantes :confused: (vérifiez la hiérarchie)")
            else:
                await ctx.send(f"{user} a bien été banni !")
            await ctx.send("https://thumbs.gfycat.com/LikelyColdBasil-small.gif")


# The end.
def setup(bot):
    bot.add_cog(Ban(bot))
