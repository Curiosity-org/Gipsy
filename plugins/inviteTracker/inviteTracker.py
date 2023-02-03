"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import discord
from discord.ext import tasks, commands
from utils import Gunibot, MyContext
from bot import checks


class DatabaseInvite:
    """Represent a database invitation object"""

    guild: discord.Guild
    channel: discord.TextChannel
    user: int
    id: int
    code: int
    uses: int
    description: str

    def __init__(self, data: Tuple[Any], parent: Gunibot) -> None:
        """Constrcut the classe with the database data

        Attributes
        ----------
        parent: Gunibot
            The gunibot instance
        data: Tuple[Any]
            data
        """
        self.parent = parent
        self.guild = self.parent.get_guild(data[0])
        self.channel = self.guild.get_channel(data[1])
        self.user = data[2]
        self.id = data[3]
        self.code = data[4]
        self.uses = data[5]
        self.description = data[6]

    async def check_use(self) -> bool:
        """Return if the invitation has been used and edit if necessary

        Returns
        -------
        bool
            If the invitation was used since last update or not
        """
        invites = await self.channel.invites()
        if self.id in (invite.id for invite in invites):
            invite = [invite for invite in invites if invite.id == self.id][0]
            if invite.uses != self.uses:
                self.update(invite)
                return True
        else:
            self.delete()
        return False

    def delete(self) -> None:
        """Delete the invitation in the database"""
        query = "DELETE FROM invites WHERE id = ?"
        self.parent.db_query(query, (self.id,))

    def update(self, invite: discord.Invite) -> None:
        """Update the invite to match the given in database

        Attributes
        ----------
        invite: discord.Invite
            The invitation to update
        """
        if invite.id != self.id:
            raise ValueError("The invitation is not the current one")
        self.uses = invite.uses
        query = "UPDATE invites SET uses=? WHERE id=?;"
        self.parent.db_query(
            query,
            (
                self.uses,
                self.id,
            ),
        )

    @classmethod
    def add(cls, invite: discord.Invite, parent: Gunibot):
        """Create a new invitation in the database from a discord invitation

        Attributes
        ----------
        invite: discord.Invite
            The discord invitation
        parent: Gunibot
            The parent for which to add in the database

        Returns
        -------
        DatabaseInvite
            The database invite build with the discord invitation
        """
        query = "INSERT INTO invites VALUES (?, ?, ?, ?, ?, ?, ?);"
        parent.db_query(
            query,
            (
                invite.guild.id if invite.guild is not None else None,
                invite.channel.id,
                invite.inviter.id if invite.inviter is not None else None,
                invite.id,
                invite.code,
                invite.uses,
                "",
            ),
            astuple=True,
        )
        data = parent.db_query(
            "SELECT * FROM invites WHERE id=?",
            (invite.id,),
            astuple=True,
            fetchone=True,
        )
        return cls(data, parent)

    async def fetch_inviter(self) -> discord.User:
        """Return the user that owns the invitation

        Returns
        -------
        discord.User
            The user that owns the invite
        """
        return await self.parent.fetch_user(self.user)

    def set_description(self, description: str) -> None:
        """Change the description for the invite in the database

        Attributes
        ----------
        description: str
            The new description
        """
        query = "UPDATE invites SET description=? WHERE id=?;"
        self.parent.db_query(query, (description, self.id))

    def __eq__(self, object: Union[int, str, "Invite", discord.Invite]) -> bool:
        if isinstance(object, int):
            return self.id == object
        elif isinstance(object, str):
            return self.code == object
        elif isinstance(object, Invite):
            return self.id == object.id
        elif isinstance(object, discord.Invite):
            return self.id == object.id


class Invite(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.config_options = ["invite_log"]
        bot.get_command("config").add_command(self.invite_log)

    @commands.command(name="invite_log")
    @commands.check(checks.is_admin)
    async def invite_log(
        self, ctx: MyContext, channel: discord.TextChannel = None
    ) -> None:
        """Change le salon où sont envoyés les messages avec les invitations utilisées"""
        if channel is not None:
            channel = channel.id
        await ctx.send(
            await self.bot.sconfig.edit_config(ctx.guild.id, "invite_log", channel)
        )

    @commands.command(name="set_description")
    @commands.check(checks.is_admin)
    async def set_description(self, ctx: MyContext, code: str, *description) -> None:
        """Change the description for a invitation (e.g. website...)
        code: the code of an invitation (e.g. RXjCkvmPXn)
        """
        await self.check_invites(ctx.guild)
        invite = self.get_invite_by_code(code)
        if invite is not None:
            invite.set_description(" ".join(description))
            await ctx.send(
                await self.bot._(
                    ctx.guild.id,
                    "invite-tracker.set-description-done",
                    code=invite.code,
                )
            )
        else:
            await ctx.send(await self.bot._(ctx.guild.id, "invite-tracker.not-found"))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Called when a momber join a guild.
        This event check the join invitation

        Attributes
        ----------
        member: discord.Member
            The member who join the guild
        """
        if not member.guild.me.guild_permissions.manage_guild:
            return
        invite = await self.check_invites(member.guild)
        if invite is not None:
            channel = self.bot.server_configs[member.guild.id]["invite_log"]
            if channel is not None:
                channel = self.bot.get_channel(channel)
                if invite.description == "":
                    await channel.send(
                        await self.bot._(
                            member.guild.id,
                            "invite-tracker.join-code",
                            member=member.mention,
                            guild=member.guild,
                            code=invite.code,
                            inviter=(await invite.fetch_inviter()).mention,
                            uses=invite.uses,
                        )
                    )
                else:
                    await channel.send(
                        await self.bot._(
                            member.guild.id,
                            "invite-tracker.join-description",
                            member=member.mention,
                            guild=member.guild,
                            code=invite.code,
                            inviter=(await invite.fetch_inviter()).mention,
                            description=invite.description,
                            uses=invite.uses,
                        )
                    )

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Called when the bot is ready.
        This event refresh all the invitations in all the servers
        """
        for guild in self.bot.guilds:
            if guild.me.guild_permissions.manage_guild:
                await self.check_invites(guild)
        self.bot.log.info("Invitations successfully synced")

    async def check_invites(self, guild: discord.Guild) -> Optional[DatabaseInvite]:
        """Check for all guild invite and changes

        Attributes
        ----------
        guild: discord.Guild
            The guild for which to check the invites

        Returns
        -------
        Optional[discord.Invite]
            The last discord invite with changes detected
        """
        invites = await guild.invites()
        output_invite = None
        for invite in invites:
            database_invite = self.get_invite_by_id(invite.id)
            if database_invite is None:
                database_invite = DatabaseInvite.add(invite, self.bot)
                if invite.uses > 0:
                    output_invite = database_invite
            else:
                if await database_invite.check_use():
                    output_invite = database_invite
        for invitation in self.get_invite_by_server(guild):
            is_in = False
            for database_invite in invites:
                if invitation == database_invite:
                    is_in = True
            if not is_in:
                invitation.delete()
        return output_invite

    def get_invite_by_code(self, code: str) -> Optional[DatabaseInvite]:
        """Return a dict representing the discord invitation stored in database

        Attributes
        ----------
        code: str
            The code to look for

        Returns
        -------
        Optional[DatabaseInvite]
            The representation of the database object
        """
        query = "SELECT * FROM invites WHERE code = ?"
        data = self.bot.db_query(query, (code,), fetchone=True, astuple=True)
        if data is not tuple():
            return DatabaseInvite(data, self.bot)
        else:
            return None

    def get_invite_by_id(self, id: int) -> Optional[DatabaseInvite]:
        """Return a dict representing the discord invitation stored in database

        Attributes
        ----------
        id: int
            The id for which to look

        Returns
        -------
        Optional[DatabaseInvite]
            The representation of the database object
        """
        query = "SELECT * FROM invites WHERE id = ?"
        data = self.bot.db_query(query, (id,), fetchone=True, astuple=True)
        if data is not tuple():
            return DatabaseInvite(data, self.bot)
        else:
            return None

    def get_invite_by_server(
        self, guild: Union[int, discord.Guild]
    ) -> List[DatabaseInvite]:
        """Retrieve all invites stored in database in a guild

        Attributes
        ----------
        guild: Union[int, discord.Guild]
            The guild for which to look

        Returns
        -------
        List[DatabaseInvite]
            The list of invitations found
        """
        if isinstance(guild, discord.Guild):
            guild = guild.id
        query = f"SELECT * FROM invites WHERE guild = ?;"
        datas = self.bot.db_query(query, (guild,), astuple=True)
        return [DatabaseInvite(data, self.bot) for data in datas]

config = {}
async def setup(bot:Gunibot=None, plugin_config:dict=None):
    if bot is not None:
        await bot.add_cog(Invite(bot), icon="👋")
    if plugin_config is not None:
        global config
        config.update(plugin_config)

