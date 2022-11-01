import typing
import discord
from discord.ext import tasks, commands
from utils import Gunibot, MyContext
import bot.args as args


class ChannelArchive(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.config_options = ["archive_category", "archive_duration"]
        self.update_loop.start()

        bot.get_command("config").add_command(self.config_archive_category)
        bot.get_command("config").add_command(self.config_archive_duration)

    @commands.command(name="archive_category")
    async def config_archive_category(
        self, ctx: MyContext, *, category: discord.CategoryChannel
    ):
        await ctx.send(
            await self.bot.sconfig.edit_config(
                ctx.guild.id, "archive_category", category.id
            )
        )

    @commands.command(name="archive_duration")
    async def config_archive_duration(
        self, ctx: MyContext, duration: commands.Greedy[args.tempdelta]
    ):
        duration = sum(duration)
        if duration == 0:
            if ctx.message.content.split(" ")[-1] != "archive_duration":
                await ctx.send(
                    await self.bot._(ctx.guild.id, "sconfig.invalid-duration")
                )
                return
            duration = None
        x = await self.bot.sconfig.edit_config(
            ctx.guild.id, "archive_duration", duration
        )
        await ctx.send(x)

    def cog_unload(self):
        self.update_loop.cancel()

    async def add_to_archive(self, guild: discord.Guild, channel: discord.TextChannel):
        # Get archive category
        config = self.bot.server_configs[guild.id]
        archive = self.bot.get_channel(config["archive_category"])

        # Move channel
        await channel.move(
            beginning=True,
            category=archive,
            sync_permissions=True,
            reason="Channel archived",
        )

        # Add record to database
        query = "INSERT INTO archive (guild, channel) VALUES (?, ?)"
        self.bot.db_query(query, (guild.id, channel.id))

    async def update(
        self, guild: discord.Guild, log_channel: typing.Optional[discord.TextChannel]
    ):

        # Get archive duration
        config = self.bot.server_configs[guild.id]
        duration = config["archive_duration"]
        archive_category = config["archive_category"]
        if self.bot.get_channel(archive_category) is None:
            return

        query = f"SELECT * FROM archive WHERE guild = {guild.id}"
        records = self.bot.db_query(query, ())

        # Adding manually archived channels
        channelIds = []
        added = 0
        for channel in self.bot.get_channel(archive_category).channels:
            listed = False
            channelIds.append(channel.id)
            for record in records:
                if channel.id == record["channel"]:
                    listed = True
            if not listed:
                added += 1
                await self.add_to_archive(guild, channel)

        # Clear db records corresponding to channels outside the archive
        # category
        unarchived = 0
        for record in records:
            if self.bot.get_channel(record["channel"]) is not None:
                if (
                    self.bot.get_channel(record["channel"]).category.id
                    != archive_category
                ):
                    query = f"DELETE FROM archive WHERE channel = {record['channel']} AND guild = {guild.id}"
                    unarchived += 1
                    self.bot.db_query(query, ())

        # Clear db from deleted channel records
        removed_records = 0
        for record in records:
            if self.bot.get_channel(record["channel"]) is None:
                removed_records += 1
                query = f"DELETE FROM archive WHERE channel = {record['channel']} AND guild = {guild.id}"
                self.bot.db_query(query, ())

        # Get & delete old channels
        query = f"SELECT * FROM archive WHERE timestamp <= datetime('now','-{duration} seconds') AND guild = {guild.id}"
        records = self.bot.db_query(query, ())

        removed_channels = 0
        for record in records:
            if record_channel := self.bot.get_channel(record["channel"]):
                if record_channel.category.id == archive_category:
                    # Remove channels
                    removed_channels += 1
                    await record_channel.delete(reason="Exceeded archive duration.")

                    # Remove record
                    removed_records += 1
                    query = f"DELETE FROM archive WHERE channel = {record['channel']} AND guild = {guild.id}"
                    self.bot.db_query(query, ())

        # Send confirmation
        message = await self.bot._(
            guild.id, "archive_channel.channel_deleted", count=removed_channels
        )
        message += "\n" + await self.bot._(
            guild.id, "archive_channel.record_deleted", count=removed_records
        )
        message += "\n" + await self.bot._(
            guild.id, "archive_channel.unarchived", count=unarchived
        )
        message += "\n" + await self.bot._(
            guild.id, "archive_channel.archived", count=added
        )

        if log_channel is not None:
            await log_channel.send(
                embed=discord.Embed(
                    description=message,
                    title=await self.bot._(guild.id, "archive_channel.title-update"),
                    colour=discord.Colour.green(),
                )
            )

    # -----------------------#
    # Commande list_archive #
    # -----------------------#

    @commands.command(name="list_archive")
    @commands.guild_only()
    async def list_archive(self, ctx: MyContext):

        config = self.bot.server_configs[ctx.guild.id]
        if self.bot.get_channel(config["archive_category"]) is None:
            await ctx.send(
                await self.bot._(ctx.guild.id, "archive_channel.no-category")
            )
            return

        # Get records
        query = f"SELECT * FROM archive WHERE guild = {ctx.guild.id}"
        records = self.bot.db_query(query, ())

        # Print each record
        i = 0
        message = ""
        if len(records) > 0:
            for record in records:
                i += 1
                if i != 1:
                    message += "\n"
                if self.bot.get_channel(record["channel"]) is not None:
                    message += (
                        self.bot.get_channel(record["channel"]).mention
                        + " - "
                        + record["timestamp"]
                    )
                else:
                    message += "#deleted-channel - " + record["timestamp"]
            await ctx.send(
                embed=discord.Embed(
                    description=message,
                    title=await self.bot._(ctx.guild.id, "archive_channel.title-list"),
                    colour=discord.Colour.green(),
                )
            )

        else:
            await ctx.send(
                embed=discord.Embed(
                    description=await self.bot._(
                        ctx.guild.id, "archive_channel.no-channel"
                    ),
                    title=await self.bot._(ctx.guild.id, "archive_channel.title-list"),
                    colour=discord.Colour.green(),
                )
            )

    # -------------------------#
    # Commande update_archive #
    # -------------------------#

    @commands.command(name="update_archive")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def update_archive(self, ctx: MyContext):
        config = self.bot.server_configs[ctx.guild.id]
        if self.bot.get_channel(config["archive_category"]) is None:
            await ctx.send(
                await self.bot._(ctx.guild.id, "archive_channel.no-category")
            )
            return
        await self.update(ctx.guild, ctx.channel)

    @tasks.loop(minutes=60.0 * 24.0)
    async def update_loop(self):
        for guild in self.bot.guilds:
            config = self.bot.server_configs[guild.id]
            log_channel = self.bot.get_channel(config["logs_channel"])
            await self.update(guild, log_channel)

    # ------------------#
    # Commande archive #
    # ------------------#

    @commands.command(name="archive")
    @commands.guild_only()
    async def archive(self, ctx: MyContext, channel: discord.TextChannel = None):
        """Archive a channel"""

        # Get target channel
        if channel is None:
            channel = ctx.channel

        # Check permissions
        if (
            channel.permissions_for(ctx.author).manage_channels is True
            and channel.permissions_for(ctx.author).manage_permissions is True
        ):

            config = self.bot.server_configs[ctx.guild.id]
            if self.bot.get_channel(config["archive_category"]) is None:
                await ctx.send(
                    await self.bot._(ctx.guild.id, "archive_channel.no-category")
                )
                return

            await self.add_to_archive(ctx.guild, channel)

            # Success message
            embed = discord.Embed(
                description=await self.bot._(
                    ctx.guild.id, "archive_channel.success", channel=channel.mention
                ),
                colour=discord.Colour(51711),
            )
        else:

            # Missing permission message
            embed = discord.Embed(
                description=await self.bot._(
                    ctx.guild.id, "archive_channel.missing_permission"
                ),
                colour=0x992D22,
            )

        await ctx.send(embed=embed)


config = {}
async def setup(bot:Gunibot=None, plugin_config:dict=None):
    if bot is not None:
        await bot.add_cog(ChannelArchive(bot), icon="🗃️")
    if plugin_config is not None:
        global config
        config.update(plugin_config)
