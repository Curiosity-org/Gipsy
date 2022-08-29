import importlib
import random
import glob

import discord.abc
import discord
from discord.ext import commands
from utils import Gunibot, MyContext


class Ban(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "ban"

        self.load_friendly_ban()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id in self.friendly_ban_guilds:
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
            event_n = random.randint(0, len(self.random_events) - 1)

            # random events should always run syccessfully
            await self.random_events[event_n](self, ctx, user, reason)

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

    def load_friendly_ban(self):
        """Loads configuration and events for the friendly ban command"""
        
        # look for the configuration, gets an empty dict if it doesn't exist
        self.friendly_ban_config = self.bot.config.get("friendly_ban", {})

        # loads the guild ids from the configuration
        self.friendly_ban_guilds: list[int] = self.friendly_ban_config.get(
            "guilds",
            []
        )

        # loads the events
        self.friendly_ban_events = self.friendly_ban_config.get("events", [])
        self.systematic_events: list[function] = []
        self.random_events: list[function] = []

        for event in self.friendly_ban_events:
            chances = event.get("chances", None)
            if chances == None:
                self.systematic_events.append(
                    importlib.import_module(
                        f"plugins.ban.events.{event['module_name']}"
                    ).execute
                )
                print(f"Loaded systematic event {event['name']}")
            else:
                for _ in range(chances):
                    self.random_events.append(
                        importlib.import_module(
                            f"plugins.ban.events.{event['module_name']}"
                        ).execute
                    )
        
        # initiate the cache for the banned users roles
        self.friendly_banned_roles: dict[int,list[discord.Role]] = {}
    
    async def fake_ban(self, ctx: commands.Context, user: discord.User) -> bool:
        """Friendly ban a user
        If the ban didn't succeed, returns False"""
        # send the invitation to allow the user to rejoin the guild
        await user.send(
            await ctx.channel.create_invite(
                reason="Friendly ban",
                max_uses=1,
                unique=True,
            )
        )
        
        # store the roles somewhere to give them back to the user
        self.friendly_banned_roles[user.id] = ctx.guild.get_member(
            user.id
        ).roles
        
        try:
            await ctx.guild.kick(user, reason=f"Auto-ban!")
        except discord.Forbidden:
            await ctx.send(
                "Permissions manquantes :confused: (vérifiez la hiérarchie)"
            )
            return False
        return True

# The end.
async def setup(bot):
    await bot.add_cog(Ban(bot))
