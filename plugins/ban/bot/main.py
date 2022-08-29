import random

import discord.abc
import discord
from discord.ext import commands
from utils import Gunibot, MyContext


class Ban(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "ban"

        self.friendly_banned_roles: dict[int,list[discord.Role]] = {}

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id in self.bot.config.get("friendly_ban", []):
            if member.id in self.friendly_banned_roles:
                # Give the roles back to the users
                for role in self.friendly_banned_roles.pop(member.id):
                    if role.id != role.guild.id: # We ignore the @everyone role
                        await member.add_roles(role)

    # ------------------#
    # Commande /ban    #
    # ------------------#

    @commands.command(name="ban")
    @commands.guild_only()
    @commands.has_guild_permissions(ban_members=True)
    async def ban(
        self,
        ctx: MyContext,
        *,
        user: discord.User,
        reason: str = "Aucune raison donnée",
    ):
        if user == ctx.author and not ctx.guild.id in self.bot.config.get(
            "friendly_ban",
            []
        ):
            await ctx.send("Tu ne peux pas te bannir toi-même !")
            return
        if not ctx.guild.me.guild_permissions.ban_members:
            await ctx.send("Permission 'Bannir des membres' manquante :confused:")
            return
        member = ctx.guild.get_member(user.id)
        if (
            member is not None
            and member.roles[-1].position >= ctx.guild.me.roles[-1].position
        ):
            await ctx.send(
                "Mon rôle n'est pas assez haut pour bannir cet individu :confused:"
            )
            return

        # Normal ban
        if not ctx.guild.id in self.bot.config.get("friendly_ban", []):
            try:
                await ctx.guild.ban(
                    user,
                    delete_message_days=0,
                    reason=f"Banned by {ctx.author} ({ctx.author.id}). Reason : {reason}",
                )
            except discord.Forbidden:
                await ctx.send(
                    "Permissions manquantes :confused: (vérifiez la hiérarchie)"
                )
            else:
                await ctx.send(f"{user} a bien été banni !")
            await ctx.send("https://thumbs.gfycat.com/LikelyColdBasil-small.gif")
            return

        # Friendly ban if the guild is in the config
        else:
            # auto-ban, special Laizo
            if user == ctx.author:
                # send the invitation to allow the user to rejoin the server
                await user.send(
                    await ctx.channel.create_invite(
                        reason="Friendly ban",
                        max_uses=1,
                        unique=True,
                    )
                )
                self.friendly_banned_roles[user.id] = ctx.guild.get_member(
                    user.id
                ).roles
                try:
                    await ctx.guild.kick(user, reason=f"Auto-ban!")
                except discord.Forbidden:
                    await ctx.send(
                        "Permissions manquantes :confused: (vérifiez la hiérarchie)"
                    )
                else:
                    # Find and send some random message
                    choice = random.randint(0, 2)
                    msg = await self.bot._(
                        ctx.channel, f"ban.gunivers.autoban.{choice}"
                    )
                    await ctx.send(msg.format(ctx.author.mention, user.mention))
                    await ctx.send(
                        "https://thumbs.gfycat.com/CompleteLeafyAardwolf-size_restricted.gif"
                    )
                return

            # 1/10th chance of banning the command executor instead, Uno Reverse event.
            if random.randint(1, 10) == 1:
                await user.send(
                    await ctx.channel.create_invite(
                        reason="Friendly ban",
                        max_uses=1,
                        unique=True,
                    )
                )
                self.friendly_banned_roles[ctx.author] = ctx.author.roles
                try:
                    await ctx.guild.kick(
                        ctx.author,
                        reason=f"Banned by himself. Reason : {user} ({user.id}) used Uno Reverse card.",
                    )
                except discord.Forbidden:
                    await ctx.send(
                        "Permissions manquantes :confused: (vérifiez la hiérarchie)"
                    )
                else:
                    # Find and send some random message
                    choice = random.randint(0, 3)
                    msg = await self.bot._(
                        ctx.channel, f"ban.gunivers.selfban.{choice}"
                    )
                    await ctx.send(msg.format(ctx.author.mention, user.mention))
                    await ctx.send(
                        "https://thumbs.gfycat.com/BackInsignificantAfricanaugurbuzzard-size_restricted.gif"
                    )
                return

            # 1/10th chance of banning both banned and executor, Bothban event.
            if random.randint(1, 10) == 1:
                await user.send(
                    await ctx.channel.create_invite(
                        reason="Friendly ban",
                        max_uses=1,
                        unique=True,
                    )
                )
                self.friendly_banned_roles[user.id] = ctx.guild.get_member(user.id).roles
                self.friendly_banned_roles[ctx.author.id] = ctx.author.roles
                try:
                    await ctx.guild.kick(
                        user,
                        reason=f"Banned by {ctx.author} ({ctx.author.id}). Reason : {reason}",
                    )
                except discord.Forbidden:
                    await ctx.send(
                        "Permissions manquantes :confused: (vérifiez la hiérarchie)"
                    )
                else:
                    await user.send(
                    await ctx.channel.create_invite(
                        reason="Friendly ban",
                        max_uses=1,
                        unique=True,
                    )
                )
                    try:
                        await ctx.guild.kick(
                            ctx.author,
                            reason=f"Banned by himself. Reason : {user} ({user.id}) banned him back.",
                        )
                    except discord.Forbidden:
                        # If there's an error when banning the author, we don't
                        # care and act like if a one-way ban happened.
                        choice = random.randint(0, 9)
                        msg = await self.bot._(
                            ctx.channel, f"ban.gunivers.ban.{choice}"
                        )
                        await ctx.send(msg.format(ctx.author.mention, user.mention))
                        await ctx.send(
                            "https://thumbs.gfycat.com/PepperyEminentIndianspinyloach-size_restricted.gif"
                        )
                    else:
                        # If there's no error, find a random message and send
                        # it.
                        choice = random.randint(0, 3)
                        msg = await self.bot._(
                            ctx.channel, f"ban.gunivers.bothban.{choice}"
                        )
                        await ctx.send(msg.format(ctx.author.mention, user.mention))
                        await ctx.send(
                            "https://thumbs.gfycat.com/BackInsignificantAfricanaugurbuzzard-size_restricted.gif"
                        )
                return

            # 1/10th chance of rickrolling people, Rickroll event.
            if random.randint(1, 10) == 1:
                await self.bot._(ctx.channel, f"ban.gunivers.rickroll")
                await ctx.send(
                    "Never gonna give you up,\nnever gonna let you down,\nnever gonna run around and ban you :musical_note:"
                )
                await ctx.send(
                    "https://thumbs.gfycat.com/VengefulDesertedHalibut-size_restricted.gif"
                )
                return

            # If ban is issued by Leirof, then Bald ban event.
            if ctx.author.id == 125722240896598016:
                await user.send(
                    await ctx.channel.create_invite(
                        reason="Friendly ban",
                        max_uses=1,
                        unique=True,
                    )
                )
                self.friendly_banned_roles[user.id] = ctx.guild.get_member(user.id).roles
                try:
                    await ctx.guild.kick(
                        user,
                        reason=f"Banned by {ctx.author} ({ctx.author.id}). Reason : {reason}",
                    )
                except discord.Forbidden:
                    await ctx.send(
                        "Permissions manquantes :confused: (vérifiez la hiérarchie)"
                    )
                else:
                    # Find and send some random message
                    choice = random.randint(0, 9)
                    msg = await self.bot._(ctx.channel, f"ban.gunivers.ban.{choice}")
                    await ctx.send(msg.format(ctx.author.mention, user.mention))
                    await ctx.send(
                        "https://thumbs.gfycat.com/PepperyEminentIndianspinyloach-size_restricted.gif"
                    )
                    await ctx.send(
                        "https://media.discordapp.net/attachments/791335982666481675/979052868915064862/Chauve_qui_peut_.png"
                    )
                return

            # else, normal ban w/ random message
            else:
                await user.send(
                    await ctx.channel.create_invite(
                        reason="Friendly ban",
                        max_uses=1,
                        unique=True,
                    )
                )
                self.friendly_banned_roles[user.id] = ctx.guild.get_member(user.id).roles
                try:
                    await ctx.guild.kick(
                        user,
                        reason=f"Banned by {ctx.author} ({ctx.author.id}). Reason : {reason}",
                    )
                except discord.Forbidden:
                    await ctx.send(
                        "Permissions manquantes :confused: (vérifiez la hiérarchie)"
                    )
                else:
                    # Find and send some random message
                    choice = random.randint(0, 9)
                    msg = await self.bot._(ctx.channel, f"ban.gunivers.ban.{choice}")
                    await ctx.send(msg.format(ctx.author.mention, user.mention))
                    await ctx.send(
                        "https://thumbs.gfycat.com/PepperyEminentIndianspinyloach-size_restricted.gif"
                    )
                return

    # ------------------#
    # Commande /rban   #
    # ------------------#
    # Parce qu'il peut être pratique de bannir tout de même

    @commands.command(name="rban")
    @commands.guild_only()
    @commands.has_guild_permissions(ban_members=True)
    async def rban(
        self,
        ctx: MyContext,
        *,
        user: discord.User,
        reason: str = "Aucune raison donnée",
    ):
        if ctx.guild.id == 125723125685026816 or ctx.guild.id == 689159304049197131:
            if user == ctx.author:
                await ctx.send("Tu ne peux pas te bannir toi-même abruti !")
                return
            if not ctx.guild.me.guild_permissions.ban_members:
                await ctx.send(
                    "Permission 'Bannir des membres' manquante, c'est con :confused:"
                )
                return
            member = ctx.guild.get_member(user.id)
            if (
                member is not None
                and member.roles[-1].position >= ctx.guild.me.roles[-1].position
            ):
                await ctx.send(
                    "Mon rôle n'est pas assez haut pour bannir cet individu :confused:"
                )
                return
            try:
                await ctx.guild.ban(
                    user,
                    delete_message_days=0,
                    reason=f"Banned by {ctx.author} ({ctx.author.id}). Reason : {reason}",
                )
            except discord.Forbidden:
                await ctx.send(
                    "Permissions manquantes :confused: (vérifiez la hiérarchie)"
                )
            else:
                await ctx.send(f"{user} a bien été banni !")
            await ctx.send("https://thumbs.gfycat.com/LikelyColdBasil-small.gif")


# The end.
async def setup(bot):
    await bot.add_cog(Ban(bot))
