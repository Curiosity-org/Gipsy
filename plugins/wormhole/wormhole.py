"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

from typing import Optional, Union

import discord
from aiohttp import ClientSession
from discord.ext import commands
from LRFutils import logs

from bot import checks
from utils import Gunibot, MyContext


def similar(msg1: discord.Message, msg2: discord.Message):
    """Check if two messages are similar. Two messages are similar if:
    - their content is the exact same
    - their attachments have the same filemane and the same size
    """
    if msg1.content != msg2.content:
        return False

    attachments1 = sorted(
        [
            (attachment.filename, attachment.size, attachment.is_spoiler())
            for attachment in msg1.attachments
        ],
        key=lambda x: x[0],
    )
    attachments2 = sorted(
        [
            (attachment.filename, attachment.size, attachment.is_spoiler())
            for attachment in msg2.attachments
        ],
        key=lambda x: x[0],
    )

    return attachments1 == attachments2


async def get_corresponding_answer(
    channel: discord.abc.Messageable, message: discord.Message
) -> discord.Message:
    "Get the corresponding answered message in other channels"
    date = message.created_at
    async for msg in channel.history(limit=20, after=date, oldest_first=True):
        if similar(message, msg):
            return msg
    async for msg in channel.history(limit=20, before=date, oldest_first=False):
        if similar(message, msg):
            return msg
    return None


async def send_message(
    msg: discord.Message,
    webhook: discord.Webhook,
    username: str,
    pp_guild: bool,
    embed_reply: discord.Embed = None,
    thread: discord.Thread = None,
):
    "Send a message into a wormhole entry"
    msg_content = []
    if len(msg.content) > 2000:
        msg_content.append(msg.content[:2000])
        msg_content.append(msg.content[2000:])
    else:
        msg_content.append(msg.content)
        
    files = []
    for attachment in msg.attachments:
        file = await attachment.to_file()
        file.spoiler = attachment.is_spoiler()
        files.append(file)
    # grab mentions from the source message
    mentions = discord.AllowedMentions(
        everyone=msg.mention_everyone, users=msg.mentions, roles=msg.role_mentions
    )
    username = (
        username.replace("{user}", msg.author.global_name or msg.author.name, 10)
        .replace("{guild}", msg.guild.name, 10)
        .replace("{channel}", msg.channel.name, 10)
    )
    avatar_url = msg.author.display_avatar
    if pp_guild:
        avatar_url = msg.guild.icon.url

    embeds = [embed for embed in msg.embeds if embed.type == "rich"]
    if embed_reply and embeds:
        while len(embeds) >= 10:
            embeds.pop()
        embeds.append(embed_reply)
    elif embed_reply:
        embeds = [embed_reply]

    if thread is None:
        new_msg: discord.WebhookMessage = await webhook.send(
            content=msg_content[0],
            files=files if len(msg_content) == 1 else [],
            embeds=embeds,
            avatar_url=avatar_url,
            username=username,
            allowed_mentions=discord.AllowedMentions.none(),
            wait=True,
        )
    else:
        new_msg: discord.WebhookMessage = await webhook.send(
            content=msg_content[0],
            files=files if len(msg_content) == 1 else [],
            embeds=embeds,
            thread=thread,
            avatar_url=avatar_url,
            username=username,
            allowed_mentions=discord.AllowedMentions.none(),
            wait=True,
        )
    # edit the message to include mentions without notifications
    if mentions.roles or mentions.users or mentions.everyone:
        await new_msg.edit(allowed_mentions=mentions)

    # If the length of the message is longer than 2000 characters, we will split it
    # Since nitro allows for a max of 4000 characters, it should be fine
    if len(msg.content) > 2000:
        await webhook.send(
            content=msg_content[1],
            avatar_url=msg.author.display_avatar,
            files=files,
            username=username,
            allowed_mentions=discord.AllowedMentions.none(),
            wait=True,
        )



class PermissionType(commands.Converter):
    "Represents a wormhole entry permission (ie. write, read or both)"
    types = ["w", "r", "wr"]

    def __init__(self, action: Union[str, int] = None):
        if isinstance(action, str):
            self.type = self.types.index(action)
        elif isinstance(action, int):
            self.type = action
        else:
            return
        self.name = self.types[self.type]

    def __repr__(self):
        return self.name

    async def convert(
        self, ctx: commands.Context, argument: str
    ):  # pylint: disable=unused-argument
        if argument in self.types:
            return PermissionType(argument)
        raise commands.errors.BadArgument("Unknown permission type")


class Wormhole:
    "Represents a wormhole into the 'wormhole_list' table"

    def __init__(
        self,
        name: str,
        privacy: bool,
        webhook_name: str,
        use_guild_icon: bool,
        owners: list[int],
        bot: Gunibot,
        channels_count: int,
    ):
        self.bot = bot
        self.name = name
        self.privacy = privacy
        self.webhook_name = webhook_name
        self.use_guild_icon = use_guild_icon
        self.owners = owners
        self.channels_count = channels_count

    def to_str(self) -> str:
        """Transform the Wormhole to a human-readable string"""
        private = self.privacy == 1
        owners: list[str] = []
        for owner in self.owners:
            user = self.bot.get_user(owner)
            owners.append(user.name if user else "Unknown user")
        are_linked_ = "is linked" if self.channels_count == 1 else "are linked"
        admins_ = "Admin" if len(owners) == 1 else "Admins"
        return (
            f"Wormhole: {self.name}\n┗━▷ Private: {private} - {admins_}: {', '.join(owners)} - "
            f"**{self.channels_count}** Discord channels {are_linked_}"
        )


class WormholeChannel:
    "Represents a wormhole entry into the 'wormhole_channel' table"

    def __init__(
        self,
        name: str,
        channel_id: int,
        guild_id: int,
        perms: str,
        webhook_id: int,
        webhook_token: str,
    ):
        self.name = name
        self.channel_id = channel_id
        self.guild_id = guild_id
        self.perms = perms
        self.webhook_id = webhook_id
        self.webhook_token = webhook_token

    def to_str(self) -> str:
        """Transform the Channel to a human-readable string"""
        perms = (
            "Write and Read"
            if self.perms == "wr"
            else "Read" if self.perms == "r" else "Write"
        )
        return (
            f"Channel: <#{self.channel_id}>\n┗━▷ Linked to"
            f"**{self.name}** - Permissions: *{perms}*"
        )


class Wormholes(commands.Cog):
    "Wormhole management commands"

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "wormhole"

    def db_get_channels_count(self, wh_name: str) -> int:
        "Get the number of channels linked to a wormhole"
        query = "SELECT 1 FROM wormhole_channel WHERE name = ?"
        return len(self.bot.db_query(query, (wh_name,), astuple=True))

    def db_get_wormholes(self):
        "Get every wormhole"
        query = "SELECT * FROM wormhole_list"
        wormholes = self.bot.db_query(query, (), astuple=True)
        # comes as: (name, privacy, webhook_name, webhook_pp)
        res: list[Wormhole] = []
        for name, privacy, wh_name_format, wh_pp in wormholes:
            query = "SELECT admin FROM wormhole_admin WHERE name = ?"
            rows = self.bot.db_query(query, (name,), astuple=True)
            # come as: (admin,)
            owners: list[int] = [row[0] for row in rows]
            channels = self.db_get_channels_count(name)
            res.append(
                Wormhole(
                    name, privacy, wh_name_format, wh_pp, owners, self.bot, channels
                )
            )
        return res

    def db_get_wh_from_name(self, wh_name: str):
        "Get a wormhole from its name"
        query = "SELECT * FROM wormhole_list WHERE name = ?"
        wormhole = self.bot.db_query(query, (wh_name,), astuple=True, fetchone=True)
        # comes as: (name, privacy, webhook_name, webhook_pp)
        if not wormhole:
            return None
        name, privacy, wh_name, wh_pp = wormhole
        query = "SELECT admin FROM wormhole_admin WHERE name = ?"
        rows = self.bot.db_query(query, (wh_name,), astuple=True)
        # come as: (admin,)
        owners: list[int] = [row[0] for row in rows]
        channels = self.db_get_channels_count(wh_name)
        return Wormhole(name, privacy, wh_name, wh_pp, owners, self.bot, channels)

    def db_get_wh_channels_in_guild(self, guild_id: int):
        "Get every channel linked to a wormhole in this channel"
        query = "SELECT * FROM wormhole_channel WHERE guildID = ?"
        query_res = self.bot.db_query(query, (guild_id,), astuple=True)
        # come as: (name, channelID, guildID, type, webhookID, webhookTOKEN)
        res: list[WormholeChannel] = []
        for row in query_res:
            res.append(WormholeChannel(*row))
            res[-1].id = row[0]
        return res

    def db_get_wh_channel_from_channel(self, channel_id: int):
        "Get the wormhole linked to a channel"
        query = "SELECT * FROM wormhole_channel WHERE channelID = ?"
        query_res = self.bot.db_query(query, (channel_id,), astuple=True, fetchone=True)
        # come as: (name, channelID, guildID, type, webhookID, webhookTOKEN)
        if not query_res:
            return None
        return WormholeChannel(*query_res)

    def db_get_wh_channels_from_name(self, wh_name: str):
        "Get every channel linked to a wormhole"
        query = "SELECT * FROM wormhole_channel WHERE name = ?"
        query_res = self.bot.db_query(query, (wh_name,), astuple=True)
        # come as: (name, channelID, guildID, type, webhookID, webhookTOKEN)
        res: list[WormholeChannel] = []
        for row in query_res:
            res.append(WormholeChannel(*row))
            res[-1].id = row[0]
        return res

    def db_check_is_admin(self, wormhole: str, user: int):
        """Check if the provided user is an admin of the provided wormhole"""
        query = "SELECT 1 FROM wormhole_admin WHERE name = ? AND admin = ?"
        query_res = self.bot.db_query(query, (wormhole, user))
        return len(query_res) > 0

    def db_check_wh_exists(self, wormhole: str):
        """Check if a wormhole already exist with the provided name"""
        query = "SELECT 1 FROM wormhole_list WHERE name = ?"
        query_res = self.bot.db_query(query, (wormhole,), astuple=True)
        return len(query_res) > 0

    async def db_update_webhook(
        self,
        channel: Union[discord.TextChannel, discord.Thread],
        wormhole_name: str,
    ) -> discord.Webhook:
        """Fetchs a webhook for the specified channel, updates the linked
        channels and returns the webhook.
        """
        if isinstance(channel, discord.Thread):
            new_webhook: discord.Webhook = await channel.parent.create_webhook(
                name=wormhole_name,
            )
        else:
            new_webhook: discord.Webhook = await channel.create_webhook(
                name=wormhole_name,
            )
        query = (
            "UPDATE wormhole_channel SET webhookID=?,"
            "webhookTOKEN=? WHERE name=? AND channelID=?;"
        )

        self.bot.db_query(
            query,
            (
                new_webhook.id,
                new_webhook.token,
                wormhole_name,
                channel.id,
            ),
        )  # update the webhook in the database

        return new_webhook

    async def is_media_embed_update(
        self, before: discord.Message, after: discord.Message
    ):
        "Check if a message update is only about adding any media embed"
        if before.content != after.content or before.embeds == after.embeds:
            return False
        # check if the edited embeds are only rich embeds (the only ones sendable by bots)
        new_rich_embeds = [
            embed
            for embed in after.embeds
            if embed not in before.embeds and embed.type == "rich"
        ]
        # if no rich embed has been edited, it's not a bot update, so it must be a media embed
        return len(new_rich_embeds) == 0

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Executed every time a message is deleted"""
        wh_channel = self.db_get_wh_channel_from_channel(message.channel.id)
        if not wh_channel:
            return  # Check if there is a wormhole linked to the current channel
        if "w" not in wh_channel.perms:
            return  # Check if the current channel as Write permission

        wh_targets = self.db_get_wh_channels_from_name(wh_channel.name)

        async with ClientSession() as session:
            for row in wh_targets:
                if "r" not in row.perms or row.channel_id == message.channel.id:
                    continue
                # We're starting to send the message in all the channels linked
                # to that wormhole
                channel: discord.abc.Messageable = self.bot.get_channel(row.channel_id)
                if not channel:
                    continue
                webhook = discord.Webhook.partial(
                    row.webhook_id, row.webhook_token, session=session
                )
                oldmessage = await get_corresponding_answer(channel, message)
                if oldmessage:
                    # The webhook try to delete the message (will work only if the message
                    # belong to the webhook)
                    try:
                        await webhook.delete_message(oldmessage.id)
                    except (discord.errors.NotFound, discord.errors.Forbidden):
                        pass
                    try:
                        await oldmessage.delete()
                    except (discord.errors.NotFound, discord.errors.Forbidden):
                        pass

    @commands.Cog.listener()
    async def on_message_edit(
        self, old_message: discord.Message, new_message: discord.Message
    ):
        """Executed every time a message is edited"""
        if (
            "wormhole unlink" in old_message.content
            or "wh unlink" in old_message.content
        ):
            return
        if await self.is_media_embed_update(old_message, new_message):
            return
        wh_channel = self.db_get_wh_channel_from_channel(new_message.channel.id)
        if not wh_channel:
            return  # Check if there is a wormhole linked to the current channel
        if "w" not in wh_channel.perms:
            return  # Check if the current channel as Write permission

        # If the sender is a webhook used by the wormhole, then we don't want to send the message
        if (
            old_message.author.id == wh_channel.webhook_id
        ):  # sender id is the webhook used here
            return

        wh_targets = self.db_get_wh_channels_from_name(wh_channel.name)

        async with ClientSession() as session:
            for row in wh_targets:
                if "r" not in row.perms or row.channel_id == old_message.channel.id:
                    continue
                # We're starting to send the message in all the channels linked
                # to that wormhole
                channel: discord.abc.Messageable = self.bot.get_channel(row.channel_id)
                embeds = new_message.embeds.copy()

                if not channel:
                    continue
                webhook = discord.Webhook.partial(
                    row.webhook_id, row.webhook_token, session=session
                )

                if old_message.reference is not None:
                    reply = await old_message.channel.fetch_message(
                        old_message.reference.message_id
                    )
                    reply = await get_corresponding_answer(channel, reply)
                    if reply is None:
                        embeds.append(
                            discord.Embed(
                                description=await self.bot._(
                                    old_message.guild.id, "wormhole.reply_notfound"
                                ),
                                colour=0x2F3136,
                            )
                        )
                    else:
                        content = reply.content.replace("\n", " ")
                        if len(content) > 80:
                            content = content[:80] + "..."
                        embeds.append(
                            discord.Embed(
                                description=await self.bot._(
                                    old_message.guild.id,
                                    "wormhole.reply_to",
                                    link=reply.jump_url,
                                ),
                                colour=0x2F3136,
                            ).set_footer(
                                text=content, icon_url=reply.author.display_avatar
                            )
                        )

                oldmessage = await get_corresponding_answer(channel, old_message)
                if oldmessage is None:
                    continue

                try:
                    if isinstance(channel, discord.Thread):
                        await webhook.edit_message(
                            oldmessage.id,
                            content=new_message.content,
                            embeds=embeds,
                            allowed_mentions=None,
                            thread=channel,
                        )
                    else:
                        await webhook.edit_message(
                            oldmessage.id,
                            content=new_message.content,
                            embeds=embeds,
                            allowed_mentions=None,
                        )
                except discord.NotFound:  # the webhook has been deleted
                    logs.info(
                        f"The webhook for channel {row.channel_id} for wormhole  {wh_channel.name} \
                            has been deleted and a message has not been edited."
                    )
                except (
                    discord.Forbidden
                ):  # the webhook has changed, should not be possible due
                    # to checks before
                    logs.info(
                        f"The webhook for channel {row.channel_id} for wormhole {wh_channel.name} \
                            has changed and a message has not been edited."
                    )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Executed every time a message is sent"""
        if "wormhole unlink" in message.content or "wh unlink" in message.content:
            return

        wh_channel = self.db_get_wh_channel_from_channel(message.channel.id)
        if not wh_channel:
            return  # Check if there is a wormhole linked to the current channel
        if "w" not in wh_channel.perms:
            return  # Check if the current channel as Write permission

        # If the sender is a webhook used by the wormhole, then we don't want to send the message
        if (
            message.author.id == wh_channel.webhook_id
        ):  # sender id is the webhook used here
            return

        # Getting all the other channels linked to the wormhole
        wh_targets = self.db_get_wh_channels_from_name(wh_channel.name)
        # Getting the webhook name and avatar
        wormhole = self.db_get_wh_from_name(wh_channel.name)
        if not wormhole:
            return

        async with ClientSession() as session:
            # We're starting to send the message in all the channels linked to that wormhole
            for connected_channel in wh_targets:
                if connected_channel.channel_id == message.channel.id:
                    continue

                channel: Union[discord.TextChannel, discord.Thread] = (
                    self.bot.get_channel(
                        connected_channel.channel_id,
                    )
                )

                if not channel:
                    continue
                # Get the webhook associated to the wormhole
                webhook = discord.Webhook.partial(
                    connected_channel.webhook_id,
                    connected_channel.webhook_token,
                    session=session,
                )

                embed_reply = None
                if message.reference is not None:
                    reply = await message.channel.fetch_message(
                        message.reference.message_id
                    )
                    reply = await get_corresponding_answer(channel, reply)
                    if reply is None:
                        embed_reply = discord.Embed(
                            # "https://gunivers.net"), #
                            description=await self.bot._(
                                message.guild.id, "wormhole.reply_notfound"
                            ),
                            colour=0x2F3136,  # 2F3136
                        )
                    else:
                        content = reply.content.replace("\n", " ")
                        if len(content) > 80:
                            content = content[:80] + "..."
                        embed_reply = discord.Embed(
                            # "https://gunivers.net"), #
                            description=await self.bot._(
                                message.guild.id,
                                "wormhole.reply_to",
                                link=reply.jump_url,
                            ),
                            colour=0x2F3136,  # 2F3136
                        ).set_footer(text=content, icon_url=reply.author.display_avatar)

                try:
                    await send_message(
                        message,
                        webhook,
                        wormhole.webhook_name,
                        wormhole.use_guild_icon,
                        embed_reply,
                        thread=channel if isinstance(channel, discord.Thread) else None,
                    )
                except discord.NotFound:  # the webhook has been deleted
                    new_webhook = await self.db_update_webhook(
                        channel,
                        webhook.name,
                    )

                    await send_message(
                        message,
                        new_webhook,
                        wormhole.webhook_name,
                        wormhole.use_guild_icon,
                        embed_reply,
                        thread=channel if isinstance(channel, discord.Thread) else None,
                    )  # send the message again

    @commands.group(name="wormhole", aliases=["wh"])
    @commands.guild_only()
    @commands.cooldown(2, 15, commands.BucketType.channel)
    async def wormhole(self, ctx: MyContext):
        """Connect 2 points through space-time (or 2 text channels if you prefer)"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("wormhole")

    @wormhole.command(name="add")
    async def add(
        self,
        ctx: MyContext,
        name: str,
        privacy: bool = True,
        webhook_name: str = "{user}",
        webhook_pp_guild: bool = False,
    ):
        """Create a wormhole
        webhook_name is for how names will be displayed:
        for example: "{user} - {guild}"
        will display "fantomitechno - Gunivers"
        ⚠️ The " are required if you want spaces in your webhook name
        Available variables are {user}, {guild} and {channel}
        webhook_pp_guild is for which avatar will be the profile picture of the webhook
        if True it will be the Guild from where it comes
        and if False it will be the User who sent the message
        """
        if self.db_check_wh_exists(name):
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "wormhole.error.already-exists", name=name
                )
            )
            return
        query = (
            "INSERT INTO wormhole_list (name, privacy, webhook_name, webhook_pp)"
            "VALUES (?, ?, ?, ?)"
        )
        self.bot.db_query(query, (name, privacy, webhook_name, webhook_pp_guild))
        query = "INSERT INTO wormhole_admin (name, admin) VALUES (?,?)"
        self.bot.db_query(query, (name, ctx.author.id))
        await ctx.send(
            await self.bot._(ctx.guild.id, "wormhole.success.wormhole-created")
        )

    @wormhole.command(name="link")
    @commands.check(checks.is_server_manager)
    async def link(
        self,
        ctx: MyContext,
        wormhole: str,
        perms: PermissionType = PermissionType("wr"),
    ):
        """Link the current channel to a wormhole
        Permissions are Write and/or Read, defined by their first letter
        Examples:
            - a channel with the permissions 'wr' can Send and Receive messages from the wormhole
            - a channel with 'r' can only receive
        """
        query = "SELECT * FROM wormhole_channel WHERE channelID = ?"
        row = self.bot.db_query(query, (ctx.channel.id,), fetchone=True)
        if len(row) != 0:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "wormhole.error.already-linked", c=ctx.channel
                )
            )
            return
        if not self.db_check_wh_exists(wormhole):
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "wormhole.error.not-exists", name=wormhole
                )
            )
        else:
            if not self.db_check_is_admin(wormhole, ctx.author.id):
                await ctx.send(
                    await self.bot._(ctx.guild.id, "wormhole.error.not-admin")
                )
                return
            query = (
                "INSERT INTO wormhole_channel"
                "(name, channelID, guildID, type, webhookID, webhookTOKEN)"
                "VALUES (?, ?, ?, ?, ?, ?)"
            )

            if isinstance(ctx.channel, discord.Thread):
                webhook: discord.Webhook = await ctx.channel.parent.create_webhook(
                    name=wormhole
                )
            else:
                webhook: discord.Webhook = await ctx.channel.create_webhook(
                    name=wormhole
                )

            self.bot.db_query(
                query,
                (
                    wormhole,
                    ctx.channel.id,
                    ctx.guild.id,
                    perms.name,
                    webhook.id,
                    webhook.token,
                ),
            )
            await ctx.send(
                await self.bot._(ctx.guild.id, "wormhole.success.channel-linked")
            )

    @wormhole.command(name="unlink")
    @commands.check(checks.is_server_manager)
    async def unlink(self, ctx: MyContext):
        """Unlink the current channel to a wormhole"""
        query = "SELECT * FROM wormhole_channel WHERE channelID = ?"
        wh_channel = self.bot.db_query(
            query, (ctx.channel.id,), astuple=True, fetchone=True
        )
        # comes as: (name, channelID, guildID, type, webhookID, webhookTOKEN)
        if len(wh_channel) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "wormhole.error.not-linked"))
            return
        query = "DELETE FROM wormhole_channel WHERE channelID = ? AND name = ?"
        self.bot.db_query(query, (ctx.channel.id, wh_channel[0]))
        async with ClientSession() as session:
            webhook = discord.Webhook.partial(
                wh_channel[4], wh_channel[5], session=session
            )
            await webhook.delete()
        await ctx.send(
            await self.bot._(ctx.guild.id, "wormhole.success.channel-unlinked")
        )

    @wormhole.command(name="remove", aliases=["delete"])
    async def remove(self, ctx: MyContext, wormhole: str):
        """Delete a wormhole"""
        if not self.db_check_wh_exists(wormhole):
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "wormhole.error.not-exists", name=wormhole
                )
            )
            return
        if not self.db_check_is_admin(wormhole, ctx.author.id):
            await ctx.send(await self.bot._(ctx.guild.id, "wormhole.error.not-admin"))
            return
        query = "DELETE FROM wormhole_channel WHERE name = ?"
        self.bot.db_query(query, (wormhole,))
        query = "DELETE FROM wormhole_admin WHERE name = ?"
        self.bot.db_query(query, (wormhole,))
        query = "DELETE FROM wormhole_list WHERE name = ?"
        self.bot.db_query(query, (wormhole,))
        await ctx.send(
            await self.bot._(ctx.guild.id, "wormhole.success.wormhole-deleted")
        )

    @wormhole.group(name="modify", aliases=["edit"])
    async def modify(self, ctx: MyContext):
        """Edit a wormhole"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("wormhole modify")

    @modify.command(name="privacy")
    async def modify_privacy(self, ctx: MyContext, wormhole: str, privacy: str):
        """Edit the privacy of a wormhole
        Options for privacy are "public" and "private" """
        if privacy.lower() not in ["public", "private"]:
            await ctx.send(await self.bot._(ctx.guild.id, "wormhole.error.not-privacy"))
            return
        if not self.db_check_wh_exists(wormhole):
            return await ctx.send(
                await self.bot._(
                    ctx.guild.id, "wormhole.error.not-exists", name=wormhole
                )
            )
        if not self.db_check_is_admin(wormhole, ctx.author.id):
            await ctx.send(await self.bot._(ctx.guild.id, "wormhole.error.not-admin"))
            return
        query = "UPDATE wormhole_list SET privacy = ? WHERE name = ?"
        private = privacy.lower() == "private"
        self.bot.db_query(query, (private, wormhole))
        await ctx.send(await self.bot._(ctx.guild.id, "wormhole.success.modified"))

    @modify.command(name="webhook_name")
    async def modify_webhook_name(
        self, ctx: MyContext, wormhole: str, *, webhook_name: str
    ):
        """
        Edit the name of the wormhole's webhook. Available variables:
        - {guild}: name of the guild
        - {channel}: name of the channel
        - {user}: name of the user

        For example: "!wh modify MyWH webhook_name {user} from {guild}"

        If fantomitechno send a message in a Gunivers channel linked to the wormhole "MyWH",
        the other connected channels will see the message from a webhook called
        "fantomitechno from Gunivers".
        """

        if not self.db_check_wh_exists(wormhole):
            return await ctx.send(
                await self.bot._(
                    ctx.guild.id, "wormhole.error.not-exists", name=wormhole
                )
            )
        if not self.db_check_is_admin(wormhole, ctx.author.id):
            await ctx.send(await self.bot._(ctx.guild.id, "wormhole.error.not-admin"))
            return
        query = "UPDATE wormhole_list SET webhook_name = ? WHERE name = ?"
        self.bot.db_query(query, (webhook_name, wormhole))
        await ctx.send(await self.bot._(ctx.guild.id, "wormhole.success.modified"))

    @modify.command(name="webhook_pp")
    async def modify_webhook_pp(self, ctx: MyContext, wormhole: str, webhook_pp: bool):
        """webhook_pp_guild is for which avatar will be the profile picture of the webhook
        if True it will be the Guild from where it comes
        and if False it will be the User who sent the message"""
        if not self.db_check_wh_exists(wormhole):
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "wormhole.error.not-exists", name=wormhole
                )
            )
            return
        if not self.db_check_is_admin(wormhole, ctx.author.id):
            await ctx.send(await self.bot._(ctx.guild.id, "wormhole.error.not-admin"))
            return
        query = "UPDATE wormhole_list SET webhook_pp = ? WHERE name = ?"
        self.bot.db_query(query, (webhook_pp, wormhole))
        await ctx.send(await self.bot._(ctx.guild.id, "wormhole.success.modified"))

    @wormhole.group(name="admin")
    async def admin(self, ctx: MyContext):
        """Add or remove Wormhole Admins"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("wormhole admin")

    @admin.command(name="add")
    async def admin_add(self, ctx: MyContext, wormhole: str, user: discord.User):
        """Add a user as a wormhole admin"""
        if not self.db_check_wh_exists(wormhole):
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "wormhole.error.not-exists", name=wormhole
                )
            )
            return
        if not self.db_check_is_admin(wormhole, ctx.author.id):
            await ctx.send(await self.bot._(ctx.guild.id, "wormhole.error.not-admin"))
            return
        query = "SELECT 1 FROM wormhole_admin WHERE name = ? AND admin = ?"
        is_already = len(self.bot.db_query(query, (wormhole, user.id))) > 0
        if not is_already:
            query = "INSERT INTO wormhole_admin (name, admin) VALUES (?, ?)"
            self.bot.db_query(query, (wormhole, user.id))
            await ctx.send(
                await self.bot._(ctx.guild.id, "wormhole.success.admin-added")
            )
        else:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "wormhole.error.already-admin", user=user.name
                )
            )

    @admin.command(name="remove", aliases=["revoke"])
    async def admin_remove(self, ctx: MyContext, wormhole: str, user: discord.User):
        """Revoke an admin of a wormhole"""
        if not self.db_check_wh_exists(wormhole):
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "wormhole.error.not-exists", name=wormhole
                )
            )
            return
        if not self.db_check_is_admin(wormhole, ctx.author.id):
            await ctx.send(await self.bot._(ctx.guild.id, "wormhole.error.not-admin"))
            return
        query = "SELECT 1 FROM wormhole_admin WHERE name = ? AND admin = ?"
        is_already = len(self.bot.db_query(query, (wormhole, user.id))) > 0
        if is_already:
            query = "DELETE FROM wormhole_admin WHERE admin = ? AND name = ?"
            self.bot.db_query(query, (user.id, wormhole))
            await ctx.send(
                await self.bot._(ctx.guild.id, "wormhole.success.admin-removed")
            )
        else:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "wormhole.error.not-admin", user=user.name
                )
            )

    @wormhole.group(name="list")
    async def list(self, ctx: MyContext):
        """Get a list of available wormholes or channels"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("wormhole list")

    @list.command(name="wormholes", aliases=["wh"])
    async def list_wh(self, ctx: MyContext):
        """List all wormholes"""
        wormholes = self.db_get_wormholes()
        if not wormholes:  # we can't send an empty list
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "wormhole.error.no-wormhole", p=ctx.prefix
                )
            )
            return
        txt = "\n".join(
            [w.to_str() for w in wormholes]
        )  # pylint: disable=not-an-iterable
        await ctx.send(txt)

    @list.command(name="channels")
    async def list_channel(self, ctx: MyContext):
        """List all channels linked to a Wormhole in the current server"""
        channels = self.db_get_wh_channels_in_guild(ctx.guild.id)
        if not channels:  # we can't send an empty list
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "wormhole.error.no-channel", p=ctx.prefix
                )
            )
            return
        txt = "\n".join(
            [c.to_str() for c in channels]
        )  # pylint: disable=not-an-iterable
        await ctx.send(txt)


async def setup(bot: Optional[Gunibot] = None):
    "Load the Wormholes cog"
    if bot is not None:
        await bot.add_cog(Wormholes(bot), icon="🌀")
