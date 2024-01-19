"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

from typing import List, Annotated
import asyncio

import discord
from discord.ext import commands

from utils import Gunibot, MyContext
from bot import checks


class Group:
    def __init__(
        self,
        bot: Gunibot,
        guild_id: int,
        role_id: int,
        owner_id: int,
        channel_id: int,
        privacy: bool,
    ):
        self.bot = bot
        self.role_id = role_id
        self.owner_id = owner_id
        self.channel_id = channel_id
        self.privacy = privacy
        self.guild_id = guild_id
        self.group_id = None
        self._role = None
        self._channel = None

    def role(self) -> discord.Role:
        """Get the Discord Role attached to that group"""
        if self._role is None:
            self._role = self.bot.get_guild(self.guild_id).get_role(self.role_id)
        return self._role

    def channel(self) -> discord.TextChannel:
        """Get the Discord Text Channel attached to that group"""
        if self.channel_id is None:
            return None
        if self._channel is None:
            self._channel = self.bot.get_guild(self.guild_id).get_channel(
                self.channel_id
            )
        return self._channel

    def member_is_in(self, member: discord.Member) -> bool:
        """Check if a member is part of that group (ie has the attached role)"""
        for role in member.roles:
            if role.id == self.role_id:
                return True
        return False

    def to_str(self) -> str:
        """Transform the group to a human-readable string"""
        channel = f"<#{self.channel_id}>" if self.channel_id else "None"
        private = "True" if self.privacy == 1 else "False"
        return (
            f"Group: <@&{self.role_id}> (*id : {self.role_id}*)\n"
            f"┗━▷ Owner: <@{self.owner_id}> - Channel: {channel} - Private: {private}"
        )


class GroupConverter(commands.Converter):
    """
    Convert a user argument to the corresponding group, by looking for the Role name/id/mention
    """

    async def convert(self, ctx: MyContext, arg: str) -> Group:
        try:
            # try to convert it to a role
            role = await commands.RoleConverter().convert(ctx, arg)
        except commands.BadArgument as exc:
            await ctx.send(
                await ctx.bot._(ctx.channel, "groups.error.unknown-group", g=arg),
                ephemeral=True,
            )
            raise exc
        # make sure the cog is actually loaded, let's not break everything
        if cog := ctx.bot.get_cog("Groups"):
            if res := cog.db_get_group(ctx.guild.id, role.id):
                # if group exists, we return it
                return res
        await ctx.send(
            await ctx.bot._(ctx.channel, "groups.error.unknown-group", g=arg),
            ephemeral=True,
        )
        raise commands.BadArgument()


GroupType = Annotated[Group, GroupConverter]


class Groups(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.config_options = [
            "group_allowed_role",
            "group_channel_category",
            "group_over_role",
            "max_group",
        ]
        try:
            bot.get_command("config").add_command(self.config_group_allowed_role)
            bot.get_command("config").add_command(self.config_group_channel_category)
            bot.get_command("config").add_command(self.config_group_over_role)
            bot.get_command("config").add_command(self.config_max_group)
            bot.get_command("config").add_command(self.config_backup)
        except commands.errors.CommandRegistrationError:
            pass

    @commands.command(name="group_allowed_role")
    async def config_group_allowed_role(
        self, ctx: MyContext, *, role: discord.Role = None
    ):
        """Role allowed to create groups"""
        role = role.id if isinstance(role, discord.Role) else None
        await ctx.send(
            await self.bot.sconfig.edit_config(ctx.guild.id, "group_allowed_role", role)
        )

    @commands.command(name="group_channel_category")
    async def config_group_channel_category(
        self, ctx: MyContext, *, category: discord.CategoryChannel
    ):
        """Category were group channel will be created"""
        await ctx.send(
            await self.bot.sconfig.edit_config(
                ctx.guild.id, "group_channel_category", category.id
            )
        )

    @commands.command(name="group_over_role")
    async def config_group_over_role(
        self, ctx: MyContext, *, role: discord.Role = None
    ):
        """Role under the groups roles will be created"""
        role = role.id if isinstance(role, discord.Role) else None
        await ctx.send(
            await self.bot.sconfig.edit_config(ctx.guild.id, "group_over_role", role)
        )

    @commands.command(name="max_group")
    async def config_max_group(self, ctx: MyContext, *, number: int = None):
        """Max groups by user"""
        await ctx.send(
            await self.bot.sconfig.edit_config(ctx.guild.id, "max_group", number)
        )

    @commands.group(name="config-backup", aliases=["config-bkp"])
    @commands.guild_only()
    @commands.check(checks.is_admin)
    async def config_backup(self, ctx: MyContext):
        """Create or load your server configuration"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("config-backup")

    def db_get_config(self, guild_id: int) -> List[Group]:
        """Get every group of a specific guild"""
        query = "SELECT rowid, * FROM groups WHERE guild=?"
        liste = self.bot.db_query(query, (guild_id,), astuple=True)
        # comes as: (rowid, guild, roleID, ownerID, channelID, privacy)
        res: List[Group] = list()
        for row in liste:
            res.append(Group(self.bot, *row[1:]))
            res[-1].group_id = row[0]
        return res if len(res) > 0 else None

    def db_get_group(self, guild_id: int, role_id: int) -> Group:
        """Get a specific group from its role ID"""
        query = "SELECT rowid, * FROM groups WHERE guild=? AND roleID=?;"
        res = self.bot.db_query(query, (guild_id, role_id), fetchone=True, astuple=True)
        # comes as: (rowid, guild, roleID, ownerID, channelID, privacy)
        if not res:
            return None
        group = Group(self.bot, *res[1:])
        group.group_id = res[0]
        return group

    def db_get_n_group(self, guild_id: int, owner_id) -> int:
        """Get the number of groups owned by someone in a specific guild"""
        query = "SELECT COUNT(*) as count FROM groups WHERE guild=? AND ownerID=?"
        res = self.bot.db_query(query, (guild_id, owner_id), fetchone=True)
        return res["count"]

    def db_add_groups(self, guild, role_id, owner_id, privacy) -> int:
        """Add a group into a guild
        Return the inserted row ID"""
        query = (
            "INSERT INTO groups (guild, roleID, ownerID, privacy) VALUES (?, ?, ?, ?)"
        )
        self.bot.db_query(query, (guild, role_id, owner_id, privacy))

    def db_delete_group(self, guild_id: int, to_delete) -> bool:
        """Delete a group from a guild, based on its row ID
        Return True if a row was deleted, False else"""
        query = "DELETE FROM groups WHERE guild=? AND roleID=?"
        rowcount = self.bot.db_query(query, (guild_id, to_delete), returnrowcount=True)
        return rowcount == 1

    def db_update_group_owner(self, guild_id: int, role_id, owner_id) -> bool:
        """Update a group from a guild, based on its row ID
        Return True if a row was updated, False else"""
        query = "UPDATE groups SET ownerID=? WHERE roleID=? AND guild=? "
        rowcount = self.bot.db_query(
            query, (owner_id, role_id, guild_id), returnrowcount=True
        )
        return rowcount == 1

    def db_update_group_privacy(self, guild_id: int, role_id, privacy) -> bool:
        """Update a group from a guild, based on its row ID
        Return True if a row was updated, False else"""
        query = "UPDATE groups SET privacy=? WHERE roleID=? AND guild=? "
        rowcount = self.bot.db_query(
            query, (privacy, role_id, guild_id), returnrowcount=True
        )
        return rowcount == 1

    def db_update_group_channel(self, guild_id: int, role_id, channel_id) -> bool:
        """Update a group from a guild, based on its row ID
        Return True if a row was updated, False else"""
        query = "UPDATE groups SET channelID=? WHERE roleID=? AND guild=? "
        rowcount = self.bot.db_query(
            query, (channel_id, role_id, guild_id), returnrowcount=True
        )
        return rowcount == 1

    @commands.group(name="group", aliases=["groups"])
    @commands.guild_only()
    async def group_main(self, ctx: MyContext):
        """Manage your groups"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("group")
            return

    @group_main.command(name="add")
    @commands.check(checks.can_group)
    @commands.cooldown(1, 15, commands.BucketType.guild)
    async def group_add(self, ctx: MyContext, name: str):
        """Create a new group
        The name is only one word, no space allowed

        Example: group add cool-guys"""
        # remove spaces if needed
        name = name.replace(" ", "-")
        # check if the role exists
        role = discord.utils.get(ctx.guild.roles, name=name)
        if role:
            # if the role exists, check if a group is already created with it
            check = self.db_get_group(ctx.guild.id, role.id)
            if check:
                await ctx.send(
                    await self.bot._(ctx.guild.id, "groups.error.exist", name=name)
                )
                return
        config = ctx.bot.server_configs[ctx.guild.id]
        # if the user has already too many groups and is not a server admin, we
        # abort it
        if (
            self.db_get_n_group(ctx.guild.id, ctx.author.id) >= config["max_group"]
            and not ctx.author.guild_permissions.administrator
        ):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.tomanygroup"))
            return
        # actually create the group role
        role = await ctx.guild.create_role(
            name=name, hoist=False, reason="A new group was created"
        )
        # make sure to place it correctly if needed
        if config["group_over_role"]:
            under_role = ctx.guild.get_role(config["group_over_role"])
            if under_role:
                await role.edit(position=under_role.position - 1)
        self.db_add_groups(ctx.guild.id, role.id, ctx.author.id, 1)
        # add the user into the group (cuz well...)
        await ctx.author.add_roles(role)
        await ctx.send(await self.bot._(ctx.guild.id, "groups.created", name=name))

    @group_main.command(name="remove")
    @commands.check(checks.can_group)
    async def group_remove(self, ctx: MyContext, group: GroupType):
        """Delete a group
        Use its name, role ID or mention"""
        # if user is not the group owner and neither a server admin, we abort
        if (
            group.owner_id != ctx.author.id
            and not ctx.author.guild_permissions.administrator
        ):
            return ctx.send(await self.bot._(ctx.guild.id, "groups.error.not-owner"))
        deleted = self.db_delete_group(ctx.guild.id, group.role_id)
        if deleted:  # if everything went fine
            role = group.role()
            await ctx.send(
                await self.bot._(ctx.guild.id, "groups.delete", name=role.name)
            )
            await role.delete()
            # try to get the channel
            if not (group.channel_id and group.channel()):
                return
            else:
                # remove the channel in the database
                update = self.db_update_group_channel(ctx.guild.id, group.role_id, None)
                if update:
                    # delete the channel now
                    await group.channel().delete()
                    await ctx.send(
                        await self.bot._(
                            ctx.guild.id, "groups.channel_delete", group=role.name
                        )
                    )
                else:  # oops
                    await ctx.send(
                        await self.bot._(ctx.guild.id, "groups.error.no-delete-channel")
                    )
        else:  # wtf?!
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.no-delete"))

    @group_main.command(name="register")
    @commands.check(checks.is_admin)
    async def group_register(self, ctx: MyContext, role: discord.Role):
        """Register a group from an existing role
        Use the ID, name or mention of the role you want to add to the group system"""
        role_name = role.name
        role_id = role.id
        self.db_add_groups(ctx.guild.id, role_id, ctx.author.id, 1)
        await ctx.author.add_roles(role)
        await ctx.send(
            await self.bot._(ctx.guild.id, "groups.registred", name=role_name)
        )

    @group_main.command(name="unregister")
    @commands.check(checks.is_admin)
    async def group_unregister(self, ctx: MyContext, group: GroupType):
        """Unregister a group without deleting the role
        Use his ID, name or mention"""
        role_id = group.role_id
        deleted = self.db_delete_group(ctx.guild.id, role_id)
        if deleted:  # deletion confirmed
            role_name = group.role().name
            await ctx.send(
                await self.bot._(ctx.guild.id, "groups.unregistred", name=role_name)
            )
        else:  # https://youtu.be/t3otBjVZzT0
            await ctx.send(
                await self.bot._(ctx.guild.id, "groups.error.no-unregistred")
            )

    @group_main.group(name="modify", aliases=["edit"])
    async def group_modify_main(self, ctx: MyContext):
        """Edit your groups"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("group modify")

    @group_modify_main.command(name="leader")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def group_modify_owner(
        self, ctx: MyContext, group: GroupType, user: discord.Member
    ):
        """Edit the owner of a group"""
        # if user is not the group owner and neither a server admin, we abort
        if (
            group.owner_id != ctx.author.id
            and not ctx.author.guild_permissions.administrator
        ):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.no-update"))
            return
        config = ctx.bot.server_configs[ctx.guild.id]
        # if target has too many groups and is not a server admin, we abort it
        if (
            self.db_get_n_group(ctx.guild.id, user.id) >= config["max_group"]
            and not user.guild_permissions.administrator
        ):
            await ctx.send(
                await self.bot._(ctx.guild.id, "groups.update_owner", user=user.name)
            )
            return

        # ask the target to confirm the action
        def check(reaction, user2):
            return (
                user2.id == user.id
                and str(reaction.emoji) == "✅"
                and reaction.message.id == msg.id
            )

        role_id = group.role_id
        msg = await ctx.send(
            await self.bot._(
                ctx.guild.id,
                "groups.give",
                user=user.mention,
                owner=ctx.author.name,
                group=group.role().name,
            )
        )
        await msg.add_reaction("✅")
        try:  # the target has now 60s to click on the reaction
            await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(
                await self.bot._(ctx.guild.id, "groups.error.timeout", user=user.name)
            )
        else:
            # update the database
            update = self.db_update_group_owner(ctx.guild.id, role_id, user.id)
            if update:
                await ctx.send(
                    await self.bot._(
                        ctx.guild.id,
                        "groups.update_owner",
                        owner=user.name,
                        group=group.role().name,
                    )
                )

    @group_modify_main.command(name="name")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def group_modify_name(self, ctx: MyContext, group: GroupType, name):
        """Edit the name of a group"""
        if (
            group.owner_id != ctx.author.id
            and not ctx.author.guild_permissions.administrator
        ):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.no-update"))
            return
        role_name = group.role().name
        # let's edit role accordingly
        await group.role().edit(name=name)
        # if we should also update the channel name
        if group.channel_id is not None and role_name.lower() == group.channel().name:
            await group.channel().edit(name=name)
        await ctx.send(
            await self.bot._(
                ctx.guild.id, "groups.update_name", name=name, group=role_name
            )
        )

    @group_modify_main.command(name="privacy")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def group_modify_privacy(
        self, ctx: MyContext, group: GroupType, privacy: str
    ):
        """Edit the privacy of a group
        Privacy parameter needs to be either 'private' or 'public'

        Example: group modify privacy CoolGuys private"""
        # if user is nor group owner nor server admin, we abort
        if (
            group.owner_id != ctx.author.id
            and not ctx.author.guild_permissions.administrator
        ):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.no-update"))
            return
        # if parameter isn't what we expected
        if privacy.lower() not in ("public", "private"):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.badarg"))
            return
        # it's private if the user asked to (yes)
        private = privacy.lower() == "private"
        update = self.db_update_group_privacy(ctx.guild.id, group.role_id, private)
        if update:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id,
                    "groups.update_privacy",
                    privacy=privacy,
                    group=group.role().name,
                )
            )
        else:  # bruh
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.no-update"))

    @group_main.command(name="list")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def group_list(self, ctx: MyContext):
        """List server's groups"""
        groups = self.db_get_config(ctx.guild.id)
        if not groups:  # we can't list an empty list
            await ctx.send(
                await self.bot._(ctx.guild.id, "groups.error.no-group", p=ctx.prefix)
            )
            return
        txt = "**" + await self.bot._(ctx.guild.id, "groups.list") + "**\n"
        for group in groups:  # pylint: disable=not-an-iterable
            txt += group.to_str() + "\n\n"
        if ctx.can_send_embed:
            embed = discord.Embed(description=txt)
            await ctx.send(embed=embed)
        else:
            # allowed_mentions is to avoid pinging the owner each time
            await ctx.send(txt, allowed_mentions=discord.AllowedMentions.none())

    @group_main.command(name="join")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def group_join(self, ctx: MyContext, group: GroupType):
        """Join a group"""
        if group.privacy is None:  # group doesn't exist
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.no-exist"))
            return
        # if user is already in it (duh)
        if group.member_is_in(ctx.author):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.already-in"))
        # if group is private and user is not an admin
        elif group.privacy and not await checks.is_admin(ctx):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.private"))
        else:
            await ctx.author.add_roles(group.role(), reason="Joined a group")
            await ctx.send(
                await self.bot._(ctx.guild.id, "groups.join", name=group.role().name)
            )

    @group_main.command(name="leave")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def group_leave(self, ctx: MyContext, group: GroupType):
        """Leave a group"""
        # the owner cannot leave its own group
        if group.owner_id == ctx.author.id:
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.owner"))
            return
        # if user is not even in the group
        if not group.member_is_in(ctx.author):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.not-in"))
            return
        await ctx.author.remove_roles(group.role(), reason="Left a group")
        await ctx.send(
            await self.bot._(ctx.guild.id, "groups.leave", name=group.role().name)
        )

    @group_main.group(name="admin", aliases=["manage"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def group_admin_main(self, ctx: MyContext):
        """Manage the users in your group"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("group admin")

    @group_admin_main.command(name="list")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def group_admin_list(self, ctx: MyContext, group: GroupType):
        """Give the userlist of your group"""
        # if user is not the group owner and neither a server admin, we abort
        if (
            group.owner_id != ctx.author.id
            and not ctx.author.guild_permissions.administrator
        ):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.not-owner"))
            return
        txt = "**" + await self.bot._(ctx.guild.id, "groups.userlist") + "**\n"
        for user in group.role().members:
            txt += user.mention + "\n"
        # if we can use embeds, let's use them
        if ctx.can_send_embed:
            embed = discord.Embed(description=txt)
            await ctx.send(embed=embed)
        else:
            # allowed_mentions is to avoid pinging everyone
            await ctx.send(txt, allowed_mentions=discord.AllowedMentions.none())

    @group_admin_main.command(name="add")
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def group_admin_add(
        self, ctx: MyContext, group: GroupType, user: discord.Member
    ):
        """Add a user to a group (by force)
        Use that if the group is set to private"""
        # if user is not the group owner and neither a server admin, we abort
        if (
            group.owner_id != ctx.author.id
            and not ctx.author.guild_permissions.administrator
        ):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.not-owner"))
            return
        # if target is already in it
        if group.member_is_in(user):
            await ctx.send(
                await self.bot._(ctx.guild.id, "groups.error.already-in-user")
            )
            return
        await user.add_roles(group.role())
        await ctx.send(
            await self.bot._(
                ctx.guild.id,
                "groups.joinbyforce",
                name=group.role().name,
                user=user.name,
            )
        )

    @group_admin_main.command(name="remove")
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def group_admin_remove(
        self, ctx: MyContext, group: GroupType, user: discord.Member
    ):
        """Remove a user to a group (by force)"""
        # if user is not the group owner and neither a server admin, we abort
        if (
            group.owner_id != ctx.author.id
            and not ctx.author.guild_permissions.administrator
        ):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.not-owner"))
            return
        # if target is not in the group
        if not group.member_is_in(ctx.author):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.not-in-user"))
            return
        await user.remove_roles(group.role())
        await ctx.send(
            await self.bot._(
                ctx.guild.id,
                "groups.leavebyforce",
                name=group.role().name,
                user=user.name,
            )
        )

    @group_main.group(name="channel")
    async def group_channel_main(self, ctx: MyContext):
        """Manage your groups channels"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("group channel")

    @group_channel_main.command(name="remove")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def group_channel_remove(self, ctx: MyContext, group: GroupType):
        """Remove a group channel"""
        # if user is not the group owner and neither a server admin, we abort
        if (
            group.owner_id != ctx.author.id
            and not ctx.author.guild_permissions.administrator
        ):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.not-owner"))
            return
        # try to get the channel
        if not (group.channel_id and group.channel()):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.no-channel"))
            return
        else:
            # remove the channel in the database
            update = self.db_update_group_channel(ctx.guild.id, group.role_id, None)
            if update:
                # delete the channel now
                await group.channel().delete()
                await ctx.send(
                    await self.bot._(
                        ctx.guild.id,
                        "groups.channel_delete",
                        group=group.role().name,
                    )
                )
            else:  # oops
                await ctx.send(
                    await self.bot._(ctx.guild.id, "groups.error.no-delete-channel")
                )

    @group_channel_main.command(name="add")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def group_channel_add(self, ctx: MyContext, group: GroupType, name=None):
        """Create a private channel for you group
        Provide a channel name if you want to set it differently than the group name"""
        if not name:
            name = group.role().name
        # if user is not the group owner and neither a server admin, we abort
        if (
            group.owner_id != ctx.author.id
            and not ctx.author.guild_permissions.administrator
        ):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.not-owner"))
            return
        # if channel already exists
        if group.channel_id and group.channel():
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.channel-exist"))
            return
        # if no category has been created
        config = ctx.bot.server_configs[ctx.guild.id]
        if config["group_channel_category"] is None:
            await ctx.send(
                await self.bot._(ctx.guild.id, "groups.error.no-category", p=ctx.prefix)
            )
            return
        # if category can't be found (probably got deleted)
        categ = ctx.guild.get_channel(config["group_channel_category"])
        if categ is None:
            await ctx.send(
                await self.bot._(ctx.guild.id, "groups.error.no-category", p=ctx.prefix)
            )
            return
        # prepare channel overwrites
        overwrite = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            group.role(): discord.PermissionOverwrite(read_messages=True),
        }
        # create channel, save it, say success, end of the story.
        channel = await ctx.guild.create_text_channel(
            name=name, overwrites=overwrite, category=categ
        )
        self.db_update_group_channel(ctx.guild.id, group.role_id, channel.id)
        await ctx.send(
            await self.bot._(
                ctx.guild.id, "groups.channel-create", name=group.role().name
            )
        )

    @group_channel_main.command(name="register")
    @commands.check(checks.is_admin)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def group_channel_register(
        self, ctx: MyContext, group: GroupType, channel: discord.TextChannel
    ):
        """Register a channel as a group channel
        You'll have to edit the permissions yourself :/"""
        # if a channel already exists for that group
        if group.channel_id and group.channel():
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.channel-exist"))
            return
        # update database, say yeepee
        self.db_update_group_channel(ctx.guild.id, group.role_id, channel.id)
        await ctx.send(
            await self.bot._(
                ctx.guild.id, "groups.channel-registred", name=group.role().name
            )
        )

    @group_channel_main.command(name="unregister")
    @commands.check(checks.is_admin)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def group_channel_unregister(self, ctx: MyContext, group: GroupType):
        """Unregister a channel as a group channel
        This action will not delete the channel!"""
        # if no channel can be found
        if not (group.channel_id and group.channel()):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.no-channel"))
            return
        else:
            update = self.db_update_group_channel(ctx.guild.id, group.role_id, None)
            if update:
                await ctx.send(
                    await self.bot._(
                        ctx.guild.id,
                        "groups.channel_unregister",
                        group=group.role().name,
                    )
                )


async def setup(bot: Gunibot = None):
    if bot is not None:
        await bot.add_cog(Groups(bot), icon="🎭")
