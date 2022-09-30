import importlib
import random

import discord.abc
import discord
from discord.ext import commands
from utils import Gunibot, MyContext


class Ban(commands.Cog):
    friendly_ban_guilds: list[int]
    friendly_ban_config: dict

    friendly_ban_events: list[dict]
    systematic_events: list
    random_events: list
    friendly_ban_whitelisted_roles: list[int]
    friendly_banned_roles: dict[int, list[discord.Role]]

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "ban"

        self.load_friendly_ban()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id in self.friendly_ban_guilds:
            if member.id in self.friendly_banned_roles:
                # Give the roles back to the users

                # setup a list of the role that could not be given back
                forbidden: list[discord.Role] = []

                for role in self.friendly_banned_roles.pop(member.id):
                    if role.id != role.guild.id:  # We ignore the @everyone role
                        try:
                            await member.add_roles(role)
                        except discord.Forbidden:
                            forbidden.append(role)

                # send a message to the user if some roles could not be given back
                if len(forbidden) > 0:
                    await member.send(
                        (
                            await self.bot._(member, "ban.gunivers.missing_roles")
                            + ", ".join([role.name for role in forbidden])
                        )[:2000]
                    )

    async def ban_perm_check(ctx: commands.Context) -> bool:
        """Checks if the user has the permission to ban"""

        self: Ban = ctx.bot.get_cog("Ban")

        if ctx.guild.id not in self.friendly_ban_guilds:
            return await commands.has_guild_permissions(ban_members=True).predicate(ctx)
        else:
            for role in ctx.author.roles:
                if role.id in self.friendly_ban_whitelisted_roles:
                    return True

            return await commands.has_guild_permissions(ban_members=True).predicate(ctx)

    async def fake_ban_guild_check(ctx: commands.Context) -> bool:
        """Checks if the guild is configured for the friendly ban command"""

        self: Ban = ctx.bot.get_cog("Ban")

        return ctx.guild.id in self.friendly_ban_guilds

    # ------------------#
    # Commande /ban    #
    # ------------------#

    @commands.command(name="ban")
    @commands.guild_only()
    @commands.check(ban_perm_check)
    async def ban(
        self,
        ctx: MyContext,
        user: discord.User,
        reason: str = "Aucune raison donnée",
    ):
        "Banhammer. Use at your own risk."
        if user == ctx.author and not ctx.guild.id in self.friendly_ban_guilds:
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
        if not ctx.guild.id in self.friendly_ban_guilds:
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
            for event in self.systematic_events:
                # you should note that systematic events can return None to
                # indicate that they should be ignored
                if await event(self, ctx, user, reason):
                    return

            # Pick a random event and execute it if no systematic event has been executed
            # random events should always run successfully
            await random.choice(self.random_events)(self, ctx, user, reason)

    # ------------------#
    # Commande /rban   #
    # ------------------#
    # Because it may be useful to ban nonetheless

    @commands.command(name="rban")
    @commands.guild_only()
    @commands.check(fake_ban_guild_check)
    @commands.has_guild_permissions(ban_members=True)
    async def rban(
        self,
        ctx: MyContext,
        user: discord.User,
        reason: str = "Aucune raison donnée",
    ):
        "Bans a user. If you really don't like his face."
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

    def load_friendly_ban(self):
        """Loads configuration and events for the friendly ban command"""

        # look for the configuration, gets an empty dict if it doesn't exist
        self.friendly_ban_config = self.bot.config.get("friendly_ban", {})

        # loads the guild ids from the configuration
        self.friendly_ban_guilds: list[int] = self.friendly_ban_config.get("guilds", [])

        self.friendly_ban_whitelisted_roles: list[int] = self.friendly_ban_config.get(
            "whitelisted_roles", []
        )

        # loads the events
        self.friendly_ban_events = self.friendly_ban_config.get("events", [])
        self.systematic_events: list[function] = []
        self.random_events: list[function] = []

        for event in self.friendly_ban_events:
            chances = event.get("chances", None)
            if chances is None:
                self.systematic_events.append(
                    importlib.import_module(
                        f"plugins.ban.events.{event['module_name']}"
                    ).execute
                )
            else:
                for _ in range(chances):
                    self.random_events.append(
                        importlib.import_module(
                            f"plugins.ban.events.{event['module_name']}"
                        ).execute
                    )

        # initiate the cache for the banned users roles
        self.friendly_banned_roles: dict[int, list[discord.Role]] = {}

    async def fake_ban(
        self,
        ctx: commands.Context,
        user: discord.User,
        show_error: bool = True,
    ) -> bool:
        """Friendly ban a user
        If the ban doesn't succeed, returns False
        ctx: the context used to send the error message if necessary
        user: the user to ban
        show_error: whether to show an error message if the ban fails
        """

        # send the invitation to allow the user to rejoin the guild
        try:
            invitation = await ctx.channel.create_invite(
                reason="Friendly ban",
                max_uses=1,
                unique=True,
            )
        except discord.Forbidden:
            if show_error:
                await ctx.send(await ctx.bot._(ctx, "ban.gunivers.whoups"))

        try:
            invite_message = await user.send(invitation)
        except discord.Forbidden:
            if show_error:
                await ctx.send(await ctx.bot._(ctx, "ban.gunivers.whoups"))

        # store the roles somewhere to give them back to the user
        self.friendly_banned_roles[user.id] = ctx.guild.get_member(user.id).roles

        try:
            await ctx.guild.kick(user, reason=f"Auto-ban!")
        except discord.Forbidden:
            if show_error:
                await ctx.send(await ctx.bot._(ctx, "ban.gunivers.missing_permissions"))
            await invite_message.edit(
                content=await ctx.bot._(ctx, "ban.gunivers.urbetter")
            )
            return False
        return True


# The end.
async def setup(bot):
    await bot.add_cog(Ban(bot))
