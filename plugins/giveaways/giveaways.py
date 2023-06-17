"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import datetime
import random
import time
from marshal import dumps, loads
from typing import Any, Optional, Sequence, Union

import discord
import emoji
from discord import app_commands
from discord.ext import commands, tasks

from bot import args, checks
from utils import Gunibot, MyContext


class Giveaways(commands.Cog):
    "Manage giveaways in your server"

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.config_options = ["giveaways_emojis"]
        bot.get_command("config").add_command(self.giveaways_emojis)

    async def cog_load(self):
        self.internal_task.start() # pylint: disable=no-member

    async def cog_unload(self):
        self.internal_task.cancel() # pylint: disable=no-member

    @tasks.loop(seconds=5)
    async def internal_task(self):
        "Stop expired giveaways"
        for giveaway in self.db_get_expired_giveaways():
            if not giveaway["running"]:
                continue
            serv = self.bot.get_guild(giveaway["guild"])
            if serv is None:
                continue
            winners = await self.pick_winners(serv, giveaway)
            await self.send_results(giveaway, winners)
            self.db_stop_giveaway(giveaway["rowid"])


    @commands.command(name="giveaways_emojis")
    async def giveaways_emojis(
        self, ctx: MyContext, emojis: commands.Greedy[Union[discord.Emoji, str]]
    ):
        """Set a list of usable emojis for giveaways
        Only these emojis will be usable to participate in a giveaway
        If no emoji is specified, every emoji will be usable"""
        # check if every emoji is valid
        filtered_emojis = [
            x for x in emojis if isinstance(x, discord.Emoji) or emoji.is_emoji(x)
        ]
        # if one or more emojis were invalid (couldn't be converted)
        if len(ctx.args[2]) != len(filtered_emojis):
            await ctx.send(await self.bot._(ctx.guild.id, "sconfig.invalid-emoji"))
            return
        # if user didn't specify any emoji
        if len(filtered_emojis) == 0:
            filtered_emojis = None
        else:
            # convert discord emojis to IDs if needed
            filtered_emojis = [
                str(x.id) if isinstance(x, discord.Emoji) else x
                for x in filtered_emojis
            ]
        # save result
        await ctx.send(
            await self.bot.sconfig.edit_config(ctx.guild.id, "giveaways_emojis", filtered_emojis)
        )

    def db_add_giveaway(
        self,
        channel: discord.TextChannel,
        name: str,
        message: int,
        max_entries: int,
        ends_at: Optional[datetime.datetime] = None,
    ) -> int:
        """
        Add a giveaway into the database
        channel: the channel where the giveaway started
        message: the ID of the sent message
        max_entries: the max amount of participants
        ends_at: the end date of the giveaway (null for a manual end)
        Returns: the row ID of the giveaway
        """
        data = (
            channel.guild.id,
            channel.id,
            name[:64],
            max_entries,
            ends_at,
            message,
            dumps([]),
        )
        query = "INSERT INTO giveaways"\
            "(guild, channel, name, max_entries, ends_at, message, users)"\
            "VALUES (?, ?, ?, ?, ?, ?, ?)"
        rowid: int = self.bot.db_query(query, data)
        return rowid

    def db_get_giveaways(self, guild_id: int) -> list[dict]:
        """
        Get giveaways attached to a server
        guildID: the guild (server) ID
        Returns: a list of dicts containing the giveaways info
        """
        query = "SELECT rowid, * FROM giveaways WHERE guild=?"
        res: list[dict[str, Any]] = self.bot.db_query(query, (guild_id,))
        for data in res:
            data["users"] = loads(data["users"])
            data["ends_at"] = datetime.datetime.strptime(data["ends_at"], "%Y-%m-%d %H:%M:%S")
        return res

    def db_get_expired_giveaways(self) -> list[dict]:
        """
        Get every running giveaway
        Returns: a list of dicts containing the giveaways info
        """
        query = "SELECT rowid, * FROM giveaways WHERE ends_at <= ? AND running = 1"
        res: list[dict[str, Any]] = self.bot.db_query(query, (datetime.datetime.now(),))
        for data in res:
            data["users"] = loads(data["users"])
            data["ends_at"] = datetime.datetime.strptime(data["ends_at"], "%Y-%m-%d %H:%M:%S")
        return res

    def db_get_users(self, row_id: int) -> list[int] | None:
        """
        Get the users participating into a giveaway via command
        rowID: the ID of the giveaway to edit
        Returns: list of users IDs
        """
        query = "SELECT users FROM giveaways WHERE rowid=?"
        res: list[dict[str, bytes]] = self.bot.db_query(query, (row_id,))
        if len(res) == 0:
            return None
        return loads(res[0]["users"])

    def db_edit_participant(self, row_id: int, user_id: int, add: bool = True) -> bool:
        """
        Add a participant to a giveaway
        rowID: the ID of the giveaway to edit
        userID: the participant ID
        add: if we should add or remove the user
        Returns: if the operation succeed
        """
        current_participants = self.db_get_users(row_id)
        if current_participants is None:
            # means that the giveaway doesn't exist
            return False
        if add:
            if user_id in current_participants:
                # user was already participating
                return False
            current_participants = dumps(current_participants + [user_id])
        else:
            try:
                current_participants.remove(user_id)
            except ValueError:
                # user was not participating
                return False
            current_participants = dumps(current_participants)
        query = "UPDATE giveaways SET users=? WHERE rowid=?"
        rowcount = self.bot.db_query(query, (row_id, user_id), returnrowcount=True)
        return rowcount != 0

    def db_stop_giveaway(self, row_id: int) -> bool:
        """
        Stop a giveaway
        rowID: the ID of the giveaway to stop
        Returns: if the giveaway has successfully been stopped
        """
        query = "UPDATE giveaways SET running=0 WHERE rowid=?"
        rowcount = self.bot.db_query(query, (row_id,), returnrowcount=True)
        return rowcount == 1

    def db_delete_giveaway(self, row_id: int) -> bool:
        """
        Delete a giveaway from the database
        rowID: the ID of the giveaway to delete
        Returns: if the giveaway has successfully been deleted
        """
        query = "DELETE FROM giveaways WHERE rowid=?"
        rowcount = self.bot.db_query(query, (row_id,), returnrowcount=True)
        return rowcount == 1

    async def get_allowed_emojis(self, guild_id: int) -> list[discord.Emoji | str] | None:
        """Get a list of allowed emojis for a specific guild"""
        value: str | list[str] = self.bot.server_configs[guild_id]["giveaways_emojis"]
        if value is None:
            return None

        def emojis_convert(s_emoji: str) -> Union[str, discord.Emoji]:
            if s_emoji.isnumeric():
                d_em = discord.utils.get(self.bot.emojis, id=int(s_emoji))
                if d_em is not None:
                    return d_em
            return emoji.emojize(s_emoji, language="alias")

        value = [value] if isinstance(value, str) else value
        result = list(filter(None, [emojis_convert(x) for x in value]))
        if len(result) >= 0:
            return result
        return None

    @commands.hybrid_group(aliases=["gaw", "giveaways"])
    @commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    async def giveaway(self, ctx: MyContext):
        """Start or stop giveaways."""
        if ctx.subcommand_passed is None:
            await ctx.send_help("giveaways")

    @giveaway.command(name="start")
    @commands.check(checks.is_server_manager)
    async def gw_start(self, ctx: MyContext, *, settings: str):
        """Start a giveaway
        Usage"
        [p]giveaway start name: <Giveaway name>;
                    duration: <Time duration>;
                    entries: [winners count];
                    channel: [channel mention]
        Giveaway name is mandatory.
        Duration is mandatory.
        Winners count is optional (default 1).
        Channel is optional (default current channel).

        Example:
        [p]giveaway start name: Minecraft account; duration: 3d;
        [p]giveaway start name: Minecraft account; duration: 2h; channel: #announcements
        [p]giveaway start name: Minecraft account; duration: 5h 3min; entries: 5"""
        i_settings = (param.strip() for param in settings.split(';'))
        existing_giveaways: set[str] = {
            g["name"]
            for g in self.db_get_giveaways(ctx.guild.id)
        }

        # Setting all of the settings.
        settings_map = {"name": "", "duration": -1, "channel": ctx.channel, "entries": 1}
        for setting in i_settings:
            if setting.startswith("name: "):
                if setting[6:] in existing_giveaways:
                    await ctx.send(
                        await self.bot._(
                            ctx.guild.id, "giveaways.creation.invalid-name"
                        )
                    )
                    return
                else:
                    settings_map["name"] = setting[6:].strip()
            elif setting.startswith("entries: "):
                entries = setting.replace("entries: ", "").strip()
                if (not entries.isnumeric()) or (entries == "0"):
                    await ctx.send(
                        await self.bot._(
                            ctx.guild.id, "giveaways.creation.invalid-winners"
                        )
                    )
                    return
                settings_map["entries"] = int(entries)
            elif setting.startswith("duration: "):
                total = 0
                for elem in setting[10:].split():
                    total += await args.tempdelta().convert(ctx, elem)
                if total > 0:
                    settings_map["duration"] = total
            elif setting.startswith("channel: "):
                try:
                    channel = await commands.TextChannelConverter().convert(
                        ctx, setting.replace("channel: ", "")
                    )
                except commands.BadArgument:
                    await ctx.send(
                        await self.bot._(
                            ctx.guild.id, "giveaways.creation.invalid-channel"
                        )
                    )
                    return
                perms = channel.permissions_for(ctx.guild.me)
                if not (perms.send_messages or perms.embed_links):
                    await ctx.send(
                        await self.bot._(
                            ctx.guild.id, "giveaways.creation.invalid-perms"
                        )
                    )
                    return
                settings_map["channel"] = channel
        # Checking if mandatory settings are there.
        if settings_map["name"] == "":
            await ctx.send(
                await self.bot._(ctx.guild.id, "giveaways.creation.empty-name")
            )
            return
        if settings_map["duration"] == -1:
            await ctx.send(
                await self.bot._(ctx.guild.id, "giveaways.creation.empty-duration")
            )
            return
        settings_map["ends_at"] = datetime.datetime.fromtimestamp(
            round(time.time()) + settings_map["duration"]
        )
        # If the channel is too big, bugs will for sure happen, so we abort
        if len(settings_map["channel"].members) > 10000:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.too-many-members"))
            return
        # Send embed now
        try:
            title = await self.bot._(ctx.guild.id, "giveaways.embed.title")
            ends_at = await self.bot._(ctx.guild.id, "giveaways.embed.ends-at")
            emb = discord.Embed(
                title=title,
                description=settings_map["name"],
                timestamp=datetime.datetime.utcnow()
                + datetime.timedelta(seconds=settings_map["duration"]),
                color=discord.Colour.random(),
            ).set_footer(text=ends_at)
            msg: discord.Message = await settings_map["channel"].send(embed=emb)
            settings_map["message"] = msg.id
        except discord.HTTPException as exc:
            await self.bot.get_cog("Errors").on_error(exc, ctx)  # send error logs
            await ctx.send(
                await self.bot._(
                    ctx.guild.id,
                    "giveaways.creation.httpexception",
                    channel=settings_map["channel"].mention,
                )
            )
            return
        # Save settings in database
        rowid = self.db_add_giveaway(
            settings_map["channel"],
            settings_map["name"],
            settings_map["message"],
            settings_map["entries"],
            settings_map["ends_at"],
        )
        if rowid:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id,
                    "giveaways.creation.success",
                    name=settings_map["name"],
                    id=rowid,
                )
            )
        else:
            await ctx.send(
                await self.bot._(ctx.guild.id, "giveaways.something-went-wrong")
            )
        allowed_emojis = await self.get_allowed_emojis(ctx.guild.id)
        if allowed_emojis is None:
            return
        if msg.channel.permissions_for(ctx.guild.me).add_reactions:
            try:
                for allowed_emoji in allowed_emojis:
                    try:
                        await msg.add_reaction(allowed_emoji)
                    except discord.NotFound:
                        pass
            except discord.Forbidden:
                pass

    @giveaway.command(name="stop")
    @commands.check(checks.is_server_manager)
    async def gw_stop(self, ctx: MyContext, *, giveaway_name: str):
        """Stops a giveaway early so you can pick a winner
        Example:
        [p]giveaway stop Minecraft account"""
        giveaways = self.db_get_giveaways(ctx.guild.id)
        if len(giveaways) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.no-giveaway"))
            return
        filtered_giveaway = [
            x
            for x in giveaways
            if x["name"].lower() == giveaway_name.lower() or str(x["rowid"]) == giveaway_name
        ]
        if len(filtered_giveaway) == 0:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "giveaways.unknown-giveaway", p=ctx.prefix
                )
            )
            return
        giveaway = filtered_giveaway[0]
        if not giveaway["running"]:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.already-stopped"))
            return
        self.db_stop_giveaway(giveaway["rowid"])
        await self.send_results(giveaway, await self.pick_winners(ctx.guild, giveaway))

    @giveaway.command(name="delete")
    @commands.check(checks.is_server_manager)
    async def gw_delete(self, ctx: MyContext, *, giveaway_name: str):
        """
        Delete a giveaway from the database
        """
        giveaways = self.db_get_giveaways(ctx.guild.id)
        if len(giveaways) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.no-giveaway"))
            return
        filtered_giveaway = [
            x
            for x in giveaways
            if x["name"].lower() == giveaway_name.lower() or str(x["rowid"]) == giveaway_name
        ]
        if len(filtered_giveaway) == 0:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "giveaways.unknown-giveaway", p=ctx.prefix
                )
            )
            return
        giveaway = filtered_giveaway[0]
        if self.db_delete_giveaway(giveaway["rowid"]):
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.success-deleted"))
        else:
            await ctx.send(
                await self.bot._(ctx.guild.id, "giveaways.something-went-wrong")
            )

    @giveaway.command(name="pick-winners", aliases=["pick"])
    @commands.check(checks.is_admin)
    async def gw_pick(self, ctx: MyContext, *, giveaway_name: str):
        """Picks winners for the giveaway, which usually should be 1
        Example:
        [p]giveaway pick-winners Minecraft account
        (This will pick winners from all the people who entered the Minecraft account giveaway)
        """
        giveaways = self.db_get_giveaways(ctx.guild.id)
        if len(giveaways) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.no-giveaway"))
            return
        filtered_giveaway = [
            x
            for x in giveaways
            if x["name"].lower() == giveaway_name.lower() or str(x["rowid"]) == giveaway_name
        ]
        if len(filtered_giveaway) == 0:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "giveaways.unknown-giveaway", p=ctx.prefix
                )
            )
            return
        giveaway = filtered_giveaway[0]
        if giveaway["running"]:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id,
                    "giveaways.not-stopped",
                    p=ctx.prefix,
                    id=giveaway["rowid"],
                )
            )
            return
        allowed_reactions = await self.get_allowed_emojis(ctx.guild.id)
        users = set(giveaway["users"]) | await self.get_users(
            giveaway["channel"], giveaway["message"], allowed_reactions
        )
        if len(users) == 0:
            await ctx.send(
                await self.bot._(ctx.guild.id, "giveaways.picking.no-participant")
            )
            self.db_delete_giveaway(giveaway["rowid"])
        else:
            amount = min(giveaway["max_entries"], len(users))
            status = await ctx.send("Choix des gagnants...")
            winners = []
            trials = 0
            users = list(users)
            while len(winners) < amount and trials < 20:
                winner = discord.utils.get(ctx.guild.members, id=random.choice(users))
                if winner is not None:
                    winners.append(winner.mention)
                else:
                    trials += 1
            self.db_delete_giveaway(giveaway["rowid"])
            txt = await self.bot._(
                ctx.guild.id,
                "giveaways.picking.winners",
                count=amount,
                users=" ".join(winners),
                price=giveaway,
            )
            await status.edit(content=txt)

    # @giveaway.command()
    # @commands.cooldown(2, 40, commands.BucketType.user)
    # async def gw_enter(self, ctx: MyContext, *, giveaway: str):
    #     """Enter a giveaway.
    #     Example:
    #     [p]giveaway enter Minecraft account"""
    #     if ctx.author.bot:
    #         await ctx.send("Les bots ne peuvent pas participer à un giveaway !")
    #         return
    #     author = ctx.message.author

    #     giveaways = self.db_get_giveaways(ctx.guild.id)
    #     if len(giveaways) == 0:
    #         await ctx.send(await self.bot._(ctx.guild.id, "giveaways.no-giveaway"))
    #         return
    #     giveaways = [
    #         x for x in giveaways if x["name"] == giveaway or str(x["rowid"]) == giveaway
    #     ]
    #     if len(giveaways) == 0:
    #         await ctx.send(
    #             await self.bot._(
    #                 ctx.guild.id, "giveaways.unknown-giveaway", p=ctx.prefix
    #             )
    #         )
    #         return
    #     giveaway_data = giveaways[0]
    #     if author.id in giveaway_data["users"]:
    #         await ctx.send(
    #             await self.bot._(ctx.guild.id, "giveaways.already-participant")
    #         )
    #     elif not giveaway_data["running"]:
    #         await ctx.send(await self.bot._(ctx.guild.id, "giveaways.been-stopped"))
    #     else:
    #         if self.db_edit_participant(giveaway_data["rowid"], author.id):
    #             await ctx.send(
    #                 await self.bot._(
    #                     ctx.guild.id, "giveaways.subscribed", name=giveaway_data["name"]
    #                 )
    #             )
    #         else:
    #             await ctx.send(
    #                 await self.bot._(ctx.guild.id, "giveaways.something-went-wrong")
    #             )

    # @giveaway.command()
    # @commands.cooldown(2, 40, commands.BucketType.user)
    # async def gw_leave(self, ctx: MyContext, *, giveaway: str):
    #     """Leave a giveaway.
    #     Example:
    #     [p]giveaway leave Minecraft account"""
    #     if ctx.author.bot:
    #         await ctx.send("Les bots ne peuvent pas participer à un giveaway !")
    #         return
    #     author = ctx.message.author

    #     giveaways = self.db_get_giveaways(ctx.guild.id)
    #     if len(giveaways) == 0:
    #         await ctx.send(await self.bot._(ctx.guild.id, "giveaways.no-giveaway"))
    #         return
    #     giveaways = [
    #         x for x in giveaways if x["name"] == giveaway or str(x["rowid"]) == giveaway
    #     ]
    #     if len(giveaways) == 0:
    #         await ctx.send(
    #             await self.bot._(
    #                 ctx.guild.id, "giveaways.unknown-giveaway", p=ctx.prefix
    #             )
    #         )
    #         return
    #     giveaway_data = giveaways[0]
    #     if author.id not in giveaway_data["users"]:
    #         await ctx.send(await self.bot._(ctx.guild.id, "giveaways.already-left"))
    #     elif not giveaway_data["running"]:
    #         await ctx.send(await self.bot._(ctx.guild.id, "giveaways.been-stopped"))
    #     else:
    #         if self.db_edit_participant(giveaway_data["rowid"], author.id, add=False):
    #             await ctx.send(
    #                 await self.bot._(
    #                     ctx.guild.id, "giveaways.success-left", name=giveaway_data["name"]
    #                 )
    #             )
    #         else:
    #             await ctx.send(
    #                 await self.bot._(ctx.guild.id, "giveaways.something-went-wrong")
    #             )

    @giveaway.command(name="list-giveaways", alias=["list"])
    async def gw_list(self, ctx: MyContext):
        """lists all giveaways running in this server"""
        server = ctx.message.guild
        giveaways = self.db_get_giveaways(server.id)
        if len(giveaways) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.no-giveaway"))
            return
        else:
            running = [f"{x['rowid']}. {x['name']}" for x in giveaways if x["running"]]
            stopped = [
                f"{x['rowid']}. {x['name']}" for x in giveaways if not x["running"]
            ]
            text = ""
            if len(running) > 0:
                text += await self.bot._(ctx.guild.id, "giveaways.list-active")
                text += "\n\t{}".format("\n\t".join(running))
            if len(stopped) > 0:
                text += "\n\n" if len(text) > 0 else ""
                text += await self.bot._(ctx.guild.id, "giveaways.list-inactive")
                text += "\n\t{}".format("\n\t".join(stopped))
            if len(text) == 0:
                text = await self.bot._(ctx.guild.id, "giveaways.no-giveaway")
            await ctx.send(text)

    @giveaway.command(name="info")
    async def gw_info(self, ctx: MyContext, *, giveaway_name: str):
        """Get information for a giveaway
        Example:
        [p]giveaway info Minecraft account"""
        giveaways = self.db_get_giveaways(ctx.guild.id)
        if len(giveaways) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.no-giveaway"))
            return
        fileterd_giveaway = [
            x
            for x in giveaways
            if x["name"].lower() == giveaway_name.lower() or str(x["rowid"]) == giveaway_name
        ]
        if len(fileterd_giveaway) == 0:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "giveaways.unknown-giveaway", p=ctx.prefix
                )
            )
            return
        giveaway = fileterd_giveaway[0]
        allowed_reactions = await self.get_allowed_emojis(ctx.guild.id)
        entries = len(
            set(giveaway["users"])
            | await self.get_users(
                giveaway["channel"], giveaway["message"], allowed_reactions
            )
        )
        start, end = datetime.datetime.now(), giveaway["ends_at"]
        if start < end:
            time_left = await self.bot.get_cog("TimeCog").time_delta(
                end, start, "fr", precision=0
            )
        elif start == end:
            time_left = await self.bot._(ctx.guild.id, "giveaways.info.soon")
        else:
            time_left = await self.bot._(ctx.guild.id, "giveaways.info.ended")
        name = giveaway["name"]
        await ctx.send(
            await self.bot._(
                ctx.guild.id,
                "giveaways.info.summary",
                name=name,
                time=time_left,
                nbr=entries,
                channel=giveaway["channel"],
            )
        )

    async def get_users(
        self,
        channel_id: int,
        message_id: int,
        allowed_reactions: Sequence[Union[discord.Emoji, str]] | None,
    ):
        """Get users who reacted to a message"""
        channel: discord.TextChannel = self.bot.get_channel(channel_id)
        if channel is None:
            return set()
        message: discord.Message = await channel.fetch_message(message_id)
        if message is None or message.author != self.bot.user:
            return set()
        users: set[int] = set()
        for react in message.reactions:
            if allowed_reactions is None or react.emoji in allowed_reactions:
                async for user in react.users():
                    if not user.bot:
                        users.add(user.id)
        return users

    async def edit_embed(
        self, channel: discord.TextChannel, message_id: int, winners: list[discord.Member]
    ) -> Optional[int]:
        """Edit the embed to display results
        Returns the embed color if the embed was found, None else"""
        message: discord.Message = await channel.fetch_message(message_id)
        if (
            message is None
            or message.author != self.bot.user
            or len(message.embeds) == 0
        ):
            return None
        emb: discord.Embed = message.embeds[0]
        emb.set_footer(text=await self.bot._(channel, "giveaways.embed.ended-at"))
        emb.description = await self.bot._(
            channel,
            "giveaways.embed.desc",
            price=emb.description,
            winners=" ".join([x.mention for x in winners]),
        )
        await message.edit(embed=emb)
        return emb.color.value if emb.color else None

    async def pick_winners(
        self, guild: discord.Guild, giveaway: dict
    ) -> list[discord.Member]:
        """Select the winner of a giveaway, from both participants using the command and using the
        message reactions

        Returns a list of members
        """
        allowed_reactions = await self.get_allowed_emojis(guild.id)
        users = set(giveaway["users"]) | await self.get_users(
            giveaway["channel"], giveaway["message"], allowed_reactions
        )
        if len(users) == 0:
            return []
        else:
            amount = min(giveaway["max_entries"], len(users))
            winners = []
            trials = 0
            users = list(users)
            while len(winners) < amount and trials < 20:
                winner = discord.utils.get(guild.members, id=random.choice(users))
                if winner is not None:
                    winners.append(winner)
                else:
                    trials += 1
        return winners

    async def send_results(self, giveaway: dict, winners: list[discord.Member]):
        """Send the giveaway results in a new embed"""
        self.bot.log.info(f"Giveaway '{giveaway['name']}' has stopped")
        channel: discord.TextChannel = self.bot.get_channel(giveaway["channel"])
        if channel is None:
            return None
        emb_color = await self.edit_embed(channel, giveaway["message"], winners)
        if emb_color is None:
            # old embed wasn't found, we select a new color
            emb_color = discord.Colour.random()
        win = await self.bot._(
            channel,
            "giveaways.embed.winners",
            count=len(winners),
            winner=" ".join([x.mention for x in winners]),
        )
        desc = "{}: {} \n\n{}".format( # pylint: disable=consider-using-f-string
            await self.bot._(channel, "giveaways.embed.price"), giveaway["name"], win
        )
        emb = discord.Embed(
            title="Giveaway is over!", description=desc, color=emb_color
        )
        await channel.send(embed=emb)
        self.db_delete_giveaway(giveaway["rowid"])


async def setup(bot: Gunibot | None = None):
    if bot is not None:
        await bot.add_cog(Giveaways(bot), icon="🎁")
