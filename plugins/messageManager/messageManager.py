import discord
from discord.ext import commands
from utils import Gunibot
from typing import Union


# Moves a message from its original channel to a parameterized channel
# using a given webhook
async def moveMessage(msg: discord.Message, webhook: discord.Webhook, thread: discord.Thread = None):
    files = [await x.to_file() for x in msg.attachments]
    # grab mentions from the source message
    mentions = discord.AllowedMentions(
        everyone=msg.mention_everyone, users=msg.mentions, roles=msg.role_mentions
    )
    
    kargs = {
        "content": msg.content,
        "files": files,
        "embeds": msg.embeds,
        "avatar_url": msg.author.display_avatar,
        "username": msg.author.name,
        "allowed_mentions": discord.AllowedMentions.none(),
        "wait": True,
    }
    if thread:
        kargs["thread"] = thread

    new_msg: discord.WebhookMessage = await webhook.send(**kargs)

    # edit the message to include mentions without notifications
    if mentions.roles or mentions.users or mentions.everyone:
        await new_msg.edit(allowed_mentions=mentions)
    await msg.delete()


class MessageManager(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "messageManager"

    # -------------------#
    # Command /imitate #
    # -------------------#

    @commands.command(name="imitate")
    @commands.guild_only()
    async def imitate(
        self, ctx: commands.Context, user: discord.User = None, *, text=None
    ):
        """Say something with someone else's appearance"""

        if (
            user
            and text
            and ctx.channel.permissions_for(ctx.author).manage_messages
            and ctx.channel.permissions_for(ctx.author).manage_nicknames
        ):
            # Create a webhook in the image of the targeted member
            webhook = await ctx.channel.create_webhook(name=user.name)
            await webhook.send(content=text, avatar_url=user.display_avatar)

            # Deletes the original message as well as the webhook
            await webhook.delete()
            await ctx.message.delete()

    # ----------------#
    # Command /move #
    # ----------------#

    @commands.command(names="move", aliases=["mv"])
    @commands.guild_only()
    async def move(
        self,
        ctx: commands.Context,
        msg: discord.Message,
        channel: Union[discord.abc.Messageable, str],
        *,
        confirm=True,
    ):
        """Move a message in another channel"""

        if isinstance(channel, str):
            try:
                channel = self.bot.get_channel(int(channel.replace("<#", "").replace(">", "")))
            except BaseException:
                try:
                    channel = await ctx.guild.create_thread(int(channel.replace("<#", "").replace(">", "")))
                except BaseException:
                    await ctx.send(
                        await self.bot._(ctx.guild.id, "message_manager.no-channel")
                    )
                    return
        
        if not isinstance(channel, discord.abc.Messageable):
            await ctx.send(await self.bot._(ctx.guild.id, "message_manager.no-channel"))
            return

        author = channel.guild.get_member(ctx.author.id)

        # Check bot permissions
        perm1: discord.Permissions = ctx.channel.permissions_for(ctx.guild.me)
        perm2: discord.Permissions = channel.permissions_for(channel.guild.me)

        if not (
            perm1.read_messages
            and perm1.read_message_history
            and perm1.manage_messages
            and perm2.manage_messages
        ):
            await ctx.send(
                await self.bot._(ctx.guild.id, "message_manager.moveall.missing-perm")
            )
            self.bot.log.info(
                f'Alakon - /move: Missing permissions on guild "{ctx.guild.name}"'
            )
            return

        # Check permission
        if (
            not ctx.channel.permissions_for(ctx.author).manage_messages
            or not ctx.channel.permissions_for(ctx.author).read_messages
            or not ctx.channel.permissions_for(ctx.author).read_message_history
            or not channel.permissions_for(author).manage_messages
        ):
            embed = discord.Embed(
                description=await self.bot._(
                    ctx.guild.id, "message_manager.permission"
                ),
                colour=discord.Colour.red(),
            )
            await ctx.send(embed=embed)
            return

        dest = channel
        thread = None
        if isinstance(channel, discord.Thread):
            thread = channel
            channel = thread.parent

        # Creates a webhook to resend the message to another channel
        webhook = await channel.create_webhook(name="Gunipy Hook")
        await moveMessage(msg, webhook, thread=thread)
        await webhook.delete()

        if confirm:
            # Creates an embed to notify that the message has been moved
            embed = discord.Embed(
                description=await self.bot._(
                    ctx.guild.id,
                    "message_manager.move.confirm",
                    user=msg.author.mention,
                    channel=dest.mention,
                ),
                colour=discord.Colour(51711),
            )
            embed.set_footer(
                text=await self.bot._(
                    ctx.guild.id, "message_manager.move.footer", user=ctx.author.name
                )
            )
            await ctx.send(embed=embed)

        # Deletes the command
        await ctx.message.delete()

    # -------------------#
    # Command /moveall #
    # -------------------#

    @commands.command(names="moveall", aliases=["mva"])
    @commands.guild_only()
    async def moveall(
        self,
        ctx: commands.Context,
        msg1: discord.Message,
        msg2: discord.Message,
        channel: Union[discord.abc.Messageable, str],
        *,
        confirm=True,
    ):
        """Move several messages in another channel
        msg1 and msg2 need to be from the same channel"""

        if isinstance(channel, str):
            try:
                channel = self.bot.get_channel(int(channel.replace("<#", "").replace(">", "")))
            except BaseException:
                try:
                    channel = await ctx.guild.create_thread(int(channel.replace("<#", "").replace(">", "")))
                except BaseException:
                    await ctx.send(
                        await self.bot._(ctx.guild.id, "message_manager.no-channel")
                    )
                    return
        if not isinstance(channel, discord.abc.Messageable):
            await ctx.send(await self.bot._(ctx.guild.id, "message_manager.no-channel"))
            return

        author = channel.guild.get_member(ctx.author.id)

        # Check bot permissions
        perm1: discord.Permissions = ctx.channel.permissions_for(ctx.guild.me)
        perm2: discord.Permissions = channel.permissions_for(channel.guild.me)

        if not (
            perm1.read_messages
            and perm1.read_message_history
            and perm1.manage_messages
            and perm2.manage_messages
        ):
            await ctx.send(
                await self.bot._(ctx.guild.id, "message_manager.moveall.missing-perm")
            )
            self.bot.log.info(
                f'Alakon - /moveall: Missing permissions on guild "{ctx.guild.name}"'
            )
            return

        # Check member permissions
        if (
            not ctx.channel.permissions_for(ctx.author).manage_messages
            or not ctx.channel.permissions_for(ctx.author).read_messages
            or not ctx.channel.permissions_for(ctx.author).read_message_history
            or not channel.permissions_for(author).manage_messages
        ):
            embed = discord.Embed(
                description=await self.bot._(
                    ctx.guild.id, "message_manager.permission"
                ),
                colour=discord.Colour.red(),
            )
            await ctx.send(embed=embed)
            return

        # Send confirmation that the bot started to move messages
        embed = discord.Embed(
            description=await self.bot._(
                ctx.guild.id, "message_manager.moveall.running", channel=channel.mention
            ),
            colour=discord.Colour.blue(),
        )
        embed.set_footer(
            text=await self.bot._(
                ctx.guild.id, "message_manager.moveall.footer", user=ctx.author.name
            )
        )
        confirmation = await ctx.send(embed=embed)

        # Send a little introduction in the destination channel
        embed = discord.Embed(
            description=await self.bot._(
                ctx.guild.id,
                "message_manager.moveall.introduce",
                channel=ctx.channel.mention,
                link=confirmation.jump_url,
            ),
            colour=discord.Colour.blue(),
        )
        embed.set_footer(
            text=await self.bot._(
                ctx.guild.id, "message_manager.moveall.footer", user=ctx.author.name
            )
        )
        introduction = await channel.send(embed=embed)

        # Checks that the messages are in the same channel
        if msg1.channel != msg2.channel:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "message_manager.moveall.channel-conflict"
                )
            )
            return

        # Ensures that msg1 is indeed the first message of the two
        if msg1.created_at > msg2.created_at:
            msg2, msg1 = msg1, msg2


        dest = channel
        thread = None
        if isinstance(channel, discord.Thread):
            thread = channel
            channel = thread.parent

        # Webhook creation (common to all messages)
        webhook = await channel.create_webhook(name="Gunipy Hook")

        counter = 0

        # Retrieves the message list from msg1 to msg2
        await moveMessage(msg1, webhook, thread=thread)
        async for msg in msg1.channel.history(
            limit=200, after=msg1.created_at, before=msg2, oldest_first=True
        ):
            await moveMessage(msg, webhook, thread=thread)
            counter += 1
        await moveMessage(msg2, webhook, thread=thread)

        if counter == 0:
            await ctx.send(
                await self.bot._(ctx.guild.id, "message_manager.moveall.no-msg")
            )
            await webhook.delete()
            return

        if confirm:
            # Creates an embed to notify that the messages have been moved
            embed = discord.Embed(
                description=await self.bot._(
                    ctx.guild.id,
                    "message_manager.moveall.confirm",
                    channel=dest.mention,
                    link=introduction.jump_url,
                ),
                colour=discord.Colour.green(),
            )
            embed.set_footer(
                text=await self.bot._(
                    ctx.guild.id, "message_manager.moveall.footer", user=ctx.author.name
                )
            )
            await confirmation.edit(embed=embed)
            await ctx.message.delete()

        await webhook.delete()


# The End.
config = {}
async def setup(bot:Gunibot=None, plugin_config:dict=None):
    if bot is not None:
        await bot.add_cog(MessageManager(bot))
    if plugin_config is not None:
        global config
        config.update(plugin_config)

