import random

import discord.abc
import discord
from discord.ext import commands
from utils import Gunibot, MyContext

specialGuilds = [125723125685026816, 689159304049197131, 835218602511958116]
altearn = 835218602511958116
gunivers = 125723125685026816
curiosity = 689159304049197131
altearnInvite = "https://discord.gg/uS9cXuyeFQ"
guniversInvite = "https://discord.gg/E8qq6tN"
curiosityInvite = "https://discord.gg/jtntCqXz53"
banRolesDict = {}


class Ban(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "ban"

    @commands.Cog.listener()
    async def on_member_join(self, member):
        global banRolesDict
        # Pourquoi global ? Pour avoir un accès en écriture et pouvoir pop

        if member.guild.id in specialGuilds:
            if member.id in banRolesDict:
                # On pop pour ne pas garder inutilement la liste des rôles dans le dictionnaire
                for role in banRolesDict.pop(member.id):
                    if role.name != "@everyone":
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
        # On accède au dictionnaire des roles
        global banRolesDict

        if user == ctx.author and not ctx.guild.id in specialGuilds:
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
        if not ctx.guild.id in specialGuilds:
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

            # GUNIVERS/CURIOSITY SPECIAL CASES
        else:
            # auto-ban, special Laizo
            if user == ctx.author:
                if ctx.guild.id == gunivers:
                    await ctx.author.send(f"{guniversInvite}")
                if ctx.guild.id == curiosity:
                    await ctx.author.send(f"{curiosityInvite}")
                if ctx.guild.id == altearn:
                    await ctx.author.send(f"{altearnInvite}")
                banRolesDict[user.id] = ctx.guild.get_member(user.id).roles
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
                if ctx.guild.id == gunivers:
                    await ctx.author.send(f"{guniversInvite}")
                if ctx.guild.id == curiosity:
                    await ctx.author.send(f"{curiosityInvite}")
                if ctx.guild.id == altearn:
                    await ctx.author.send(f"{altearnInvite}")
                banRolesDict[ctx.author] = ctx.author.roles
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
                if ctx.guild.id == gunivers:
                    await user.send(f"{guniversInvite}")
                if ctx.guild.id == curiosity:
                    await user.send(f"{curiosityInvite}")
                if ctx.guild.id == altearn:
                    await user.send(f"{altearnInvite}")
                banRolesDict[user.id] = ctx.guild.get_member(user.id).roles
                banRolesDict[ctx.author.id] = ctx.author.roles
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
                    if ctx.guild.id == gunivers:
                        await ctx.author.send(f"{guniversInvite}")
                    if ctx.guild.id == curiosity:
                        await ctx.author.send(f"{curiosityInvite}")
                    if ctx.guild.id == altearn:
                        await ctx.author.send(f"{altearnInvite}")
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
                if ctx.guild.id == gunivers:
                    await user.send(f"{guniversInvite}")
                if ctx.guild.id == curiosity:
                    await user.send(f"{curiosityInvite}")
                if ctx.guild.id == altearn:
                    await user.send(f"{altearnInvite}")
                banRolesDict[user.id] = ctx.guild.get_member(user.id).roles
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
                if ctx.guild.id == gunivers:
                    await user.send(f"{guniversInvite}")
                if ctx.guild.id == curiosity:
                    await user.send(f"{curiosityInvite}")
                if ctx.guild.id == altearn:
                    await user.send(f"{altearnInvite}")
                banRolesDict[user.id] = ctx.guild.get_member(user.id).roles
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
config = {}
async def setup(bot:Gunibot=None, plugin_config:dict=None):
    if bot is not None:
        await bot.add_cog(Ban(bot))
    if plugin_config is not None:
        global config
        config.update(plugin_config)
