"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

from utils import Gunibot, MyContext
from discord.ext import commands
import discord
from bot import checks
import asyncio
from typing import List

import sys

sys.path.append("./bot")


class Group:
    def __init__(
        self,
        bot: Gunibot,
        guildID: int,
        roleID: int,
        ownerID: int,
        channelID: int,
        privacy: bool,
    ):
        self.roleID = roleID
        self.ownerID = ownerID
        self.channelID = channelID
        self.privacy = privacy
        self.guildID = guildID
        self.id = None
        self._role = None
        self._channel = None

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

    def role(self, bot: Gunibot) -> discord.Role:
        """Get the Discord Role attached to that group"""
        if self._role is None:
            self._role = bot.get_guild(self.guildID).get_role(self.roleID)
        return self._role

    def channel(self, bot: Gunibot) -> discord.TextChannel:
        """Get the Discord Text Channel attached to that group"""
        if self.channelID is None:
            return None
        if self._channel is None:
            self._channel = bot.get_guild(self.guildID).get_channel(self.channelID)
        return self._channel

    def member_is_in(self, member: discord.Member) -> bool:
        """Check if a member is part of that group (ie has the attached role)"""
        for x in member.roles:
            if x.id == self.roleID:
                return True
        return False

    def to_str(self) -> str:
        """Transform the group to a human-readable string"""
        channel = f"<#{self.channelID}>" if self.channelID else "None"
        private = "True" if self.privacy == 1 else "False"
        return f"Group: <@&{self.roleID}> (*id : {self.roleID}*)\n┗━▷ Owner: <@{self.ownerID}> - Channel: {channel} - Private: {private}"


class GroupConverter(commands.Converter):
    """Convert a user argument to the corresponding group, by looking for the Role name/id/mention"""

    async def convert(self, ctx: MyContext, arg: str) -> Group:
        try:
            # try to convert it to a role
            role = await commands.RoleConverter().convert(ctx, arg)
        except commands.BadArgument:
            raise commands.BadArgument(f'Group "{arg}" not found.')
        # make sure the cog is actually loaded, let's not break everything
        if cog := ctx.bot.get_cog("Groups"):
            if res := cog.db_get_group(ctx.guild.id, role.id):
                # if group exists, we return it
                return res
        raise commands.BadArgument(f'Group "{arg}" not found.')


class Groups(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.config_options = [
            "group_allowed_role",
            "group_channel_category",
            "group_over_role",
            "max_group",
        ]

    def db_get_config(self, guildID: int) -> List[Group]:
        """Get every group of a specific guild"""
        query = "SELECT rowid, * FROM groups WHERE guild=?"
        liste = self.bot.db_query(query, (guildID,), astuple=True)
        # comes as: (rowid, guild, roleID, ownerID, channelID, privacy)
        res: List[Group] = list()
        for row in liste:
            res.append(Group(self.bot, *row[1:]))
            res[-1].id = row[0]
        return res if len(res) > 0 else None

    def db_get_group(self, guildID: int, roleID: int) -> Group:
        """Get a specific group from its role ID"""
        query = "SELECT rowid, * FROM groups WHERE guild=? AND roleID=?;"
        res = self.bot.db_query(query, (guildID, roleID), fetchone=True, astuple=True)
        # comes as: (rowid, guild, roleID, ownerID, channelID, privacy)
        if not res:
            return None
        group = Group(self.bot, *res[1:])
        group.id = res[0]
        return group

    def db_get_n_group(self, guildID: int, ownerID) -> int:
        """Get the number of groups owned by someone in a specific guild"""
        query = "SELECT COUNT(*) as count FROM groups WHERE guild=? AND ownerID=?"
        res = self.bot.db_query(query, (guildID, ownerID), fetchone=True)
        return res["count"]

    def db_add_groups(self, guild, roleID, ownerID, privacy) -> int:
        """Add a group into a guild
        Return the inserted row ID"""
        query = (
            "INSERT INTO groups (guild, roleID, ownerID, privacy) VALUES (?, ?, ?, ?)"
        )
        self.bot.db_query(query, (guild, roleID, ownerID, privacy))

    def db_delete_group(self, guildID: int, toDelete) -> bool:
        """Delete a group from a guild, based on its row ID
        Return True if a row was deleted, False else"""
        query = "DELETE FROM groups WHERE guild=? AND roleID=?"
        rowcount = self.bot.db_query(query, (guildID, toDelete), returnrowcount=True)
        return rowcount == 1

    def db_update_group_owner(self, guildID: int, roleID, ownerID) -> bool:
        """Update a group from a guild, based on its row ID
        Return True if a row was updated, False else"""
        query = "UPDATE groups SET ownerID=? WHERE roleID=? AND guild=? "
        rowcount = self.bot.db_query(
            query, (ownerID, roleID, guildID), returnrowcount=True
        )
        return rowcount == 1

    def db_update_group_privacy(self, guildID: int, roleID, privacy) -> bool:
        """Update a group from a guild, based on its row ID
        Return True if a row was updated, False else"""
        query = "UPDATE groups SET privacy=? WHERE roleID=? AND guild=? "
        rowcount = self.bot.db_query(
            query, (privacy, roleID, guildID), returnrowcount=True
        )
        return rowcount == 1

    def db_update_group_channel(self, guildID: int, roleID, channelID) -> bool:
        """Update a group from a guild, based on its row ID
        Return True if a row was updated, False else"""
        query = "UPDATE groups SET channelID=? WHERE roleID=? AND guild=? "
        rowcount = self.bot.db_query(
            query, (channelID, roleID, guildID), returnrowcount=True
        )
        return rowcount == 1

    @commands.group(name="group", aliases=["groups"])
    @commands.guild_only()
    async def group_main(self, ctx: MyContext):
        """Manage your groups

        by fantomitechno 🦊#5973"""
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
    async def group_remove(self, ctx: MyContext, group: GroupConverter):
        """Delete a group
        Use its name, role ID or mention"""
        # if user is not the group owner and neither a server admin, we abort
        if (
            group.ownerID != ctx.author.id
            and not ctx.author.guild_permissions.administrator
        ):
            return ctx.send(await self.bot._(ctx.guild.id, "groups.error.not-owner"))
        deleted = self.db_delete_group(ctx.guild.id, group.roleID)
        if deleted:  # if everything went fine
            role = group.role(self.bot)
            await ctx.send(
                await self.bot._(ctx.guild.id, "groups.delete", name=role.name)
            )
            await role.delete()
            # try to get the channel
            if not (group.channelID and group.channel(self.bot)):
                return
            else:
                # remove the channel in the database
                update = self.db_update_group_channel(ctx.guild.id, group.roleID, None)
                if update:
                    # delete the channel now
                    await group.channel(self.bot).delete()
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
        roleName = role.name
        roleID = role.id
        self.db_add_groups(ctx.guild.id, roleID, ctx.author.id, 1)
        await ctx.author.add_roles(role)
        await ctx.send(
            await self.bot._(ctx.guild.id, "groups.registred", name=roleName)
        )

    @group_main.command(name="unregister")
    @commands.check(checks.is_admin)
    async def group_unregister(self, ctx: MyContext, group: GroupConverter):
        """Unregister a group without deleting the role
        Use his ID, name or mention"""
        roleID = group.roleID
        deleted = self.db_delete_group(ctx.guild.id, roleID)
        if deleted:  # deletion confirmed
            roleName = group.role(self.bot).name
            await ctx.send(
                await self.bot._(ctx.guild.id, "groups.unregistred", name=roleName)
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
        self, ctx: MyContext, group: GroupConverter, user: discord.Member
    ):
        """Edit the owner of a group"""
        # if user is not the group owner and neither a server admin, we abort
        if (
            group.ownerID != ctx.author.id
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

        roleID = group.roleID
        msg = await ctx.send(
            await self.bot._(
                ctx.guild.id,
                "groups.give",
                user=user.mention,
                owner=ctx.author.name,
                group=group.role(self.bot).name,
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
            update = self.db_update_group_owner(ctx.guild.id, roleID, user.id)
            if update:
                await ctx.send(
                    await self.bot._(
                        ctx.guild.id,
                        "groups.update_owner",
                        owner=user.name,
                        group=group.role(self.bot).name,
                    )
                )

    @group_modify_main.command(name="name")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def group_modify_name(self, ctx: MyContext, group: GroupConverter, name):
        """Edit the name of a group"""
        if (
            group.ownerID != ctx.author.id
            and not ctx.author.guild_permissions.administrator
        ):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.no-update"))
            return
        roleName = group.role(self.bot).name
        # let's edit role accordingly
        await group.role(self.bot).edit(name=name)
        # if we should also update the channel name
        if roleName.lower() == group.channel(self.bot).name:
            await group.channel(self.bot).edit(name=name)
        await ctx.send(
            await self.bot._(
                ctx.guild.id, "groups.update_name", name=name, group=roleName
            )
        )

    @group_modify_main.command(name="privacy")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def group_modify_privacy(
        self, ctx: MyContext, group: GroupConverter, privacy: str
    ):
        """Edit the privacy of a group
        Privacy parameter needs to be either 'private' or 'public'

        Example: group modify privacy CoolGuys private"""
        # if user is nor group owner nor server admin, we abort
        if (
            group.ownerID != ctx.author.id
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
        update = self.db_update_group_privacy(ctx.guild.id, group.roleID, private)
        if update:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id,
                    "groups.update_privacy",
                    privacy=privacy,
                    group=group.role(self.bot).name,
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
        for group in groups:
            txt += group.to_str() + "\n\n"
        if ctx.can_send_embed:
            embed = discord.Embed(description=txt)
            await ctx.send(embed=embed)
        else:
            # allowed_mentions is to avoid pinging the owner each time
            await ctx.send(txt, allowed_mentions=discord.AllowedMentions.none())

    @group_main.command(name="join")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def group_join(self, ctx: MyContext, group: GroupConverter):
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
            await ctx.author.add_roles(group.role(self.bot), reason="Joined a group")
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "groups.join", name=group.role(self.bot).name
                )
            )

    @group_main.command(name="leave")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def group_leave(self, ctx: MyContext, group: GroupConverter):
        """Leave a group"""
        # the owner cannot leave its own group
        if group.ownerID == ctx.author.id:
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.owner"))
            return
        # if user is not even in the group
        if not group.member_is_in(ctx.author):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.not-in"))
            return
        await ctx.author.remove_roles(group.role(self.bot), reason="Left a group")
        await ctx.send(
            await self.bot._(
                ctx.guild.id, "groups.leave", name=group.role(self.bot).name
            )
        )

    @group_main.group(name="admin", aliases=["manage"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def group_admin_main(self, ctx: MyContext):
        """Manage the users in your group"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("group admin")

    @group_admin_main.command(name="list")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def group_admin_list(self, ctx: MyContext, group: GroupConverter):
        """Give the userlist of your group"""
        # if user is not the group owner and neither a server admin, we abort
        if (
            group.ownerID != ctx.author.id
            and not ctx.author.guild_permissions.administrator
        ):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.not-owner"))
            return
        txt = "**" + await self.bot._(ctx.guild.id, "groups.userlist") + "**\n"
        for user in group.role(self.bot).members:
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
        self, ctx: MyContext, group: GroupConverter, user: discord.Member
    ):
        """Add a user to a group (by force)
        Use that if the group is set to private"""
        # if user is not the group owner and neither a server admin, we abort
        if (
            group.ownerID != ctx.author.id
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
        await user.add_roles(group.role(self.bot))
        await ctx.send(
            await self.bot._(
                ctx.guild.id,
                "groups.joinbyforce",
                name=group.role(self.bot).name,
                user=user.name,
            )
        )

    @group_admin_main.command(name="remove")
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def group_admin_remove(
        self, ctx: MyContext, group: GroupConverter, user: discord.Member
    ):
        """Remove a user to a group (by force)"""
        # if user is not the group owner and neither a server admin, we abort
        if (
            group.ownerID != ctx.author.id
            and not ctx.author.guild_permissions.administrator
        ):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.not-owner"))
            return
        # if target is not in the group
        if not group.member_is_in(ctx.author):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.not-in-user"))
            return
        await user.remove_roles(group.role(self.bot))
        await ctx.send(
            await self.bot._(
                ctx.guild.id,
                "groups.leavebyforce",
                name=group.role(self.bot).name,
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
    async def group_channel_remove(self, ctx: MyContext, group: GroupConverter):
        """Remove a group channel"""
        # if user is not the group owner and neither a server admin, we abort
        if (
            group.ownerID != ctx.author.id
            and not ctx.author.guild_permissions.administrator
        ):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.not-owner"))
            return
        # try to get the channel
        if not (group.channelID and group.channel(self.bot)):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.no-channel"))
            return
        else:
            # remove the channel in the database
            update = self.db_update_group_channel(ctx.guild.id, group.roleID, None)
            if update:
                # delete the channel now
                await group.channel(self.bot).delete()
                await ctx.send(
                    await self.bot._(
                        ctx.guild.id,
                        "groups.channel_delete",
                        group=group.role(self.bot).name,
                    )
                )
            else:  # oops
                await ctx.send(
                    await self.bot._(ctx.guild.id, "groups.error.no-delete-channel")
                )

    @group_channel_main.command(name="add")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def group_channel_add(self, ctx: MyContext, group: GroupConverter, name=None):
        """Create a private channel for you group
        Provide a channel name if you want to set it differently than the group name"""
        if not name:
            name = group.role(self.bot).name
        # if user is not the group owner and neither a server admin, we abort
        if (
            group.ownerID != ctx.author.id
            and not ctx.author.guild_permissions.administrator
        ):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.not-owner"))
            return
        # if channel already exists
        if group.channelID and group.channel(self.bot):
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
            group.role(self.bot): discord.PermissionOverwrite(read_messages=True),
        }
        # create channel, save it, say success, end of the story.
        channel = await ctx.guild.create_text_channel(
            name=name, overwrites=overwrite, category=categ
        )
        self.db_update_group_channel(ctx.guild.id, group.roleID, channel.id)
        await ctx.send(
            await self.bot._(
                ctx.guild.id, "groups.channel-create", name=group.role(self.bot).name
            )
        )

    @group_channel_main.command(name="register")
    @commands.check(checks.is_admin)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def group_channel_register(
        self, ctx: MyContext, group: GroupConverter, channel: discord.TextChannel
    ):
        """Register a channel as a group channel
        You'll have to edit the permissions yourself :/"""
        # if a channel already exists for that group
        if group.channelID and group.channel(self.bot):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.channel-exist"))
            return
        # update database, say yeepee
        self.db_update_group_channel(ctx.guild.id, group.roleID, channel.id)
        await ctx.send(
            await self.bot._(
                ctx.guild.id, "groups.channel-registred", name=group.role(self.bot).name
            )
        )

    @group_channel_main.command(name="unregister")
    @commands.check(checks.is_admin)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def group_channel_unregister(self, ctx: MyContext, group: GroupConverter):
        """Unregister a channel as a group channel
        This action will not delete the channel!"""
        # if no channel can be found
        if not (group.channelID and group.channel(self.bot)):
            await ctx.send(await self.bot._(ctx.guild.id, "groups.error.no-channel"))
            return
        else:
            update = self.db_update_group_channel(ctx.guild.id, group.roleID, None)
            if update:
                await ctx.send(
                    await self.bot._(
                        ctx.guild.id,
                        "groups.channel_unregister",
                        group=group.role(self.bot).name,
                    )
                )

config = {}
async def setup(bot:Gunibot=None, plugin_config:dict=None):
    if bot is not None:
        await bot.add_cog(Groups(bot), icon="🎭")
    if plugin_config is not None:
        global config
        config.update(plugin_config)
