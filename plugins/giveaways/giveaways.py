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
from typing import List, Optional, Union

import sys

sys.path.append("./bot")
import args
import sys

sys.path.append("./bot")
from bot import checks
import discord
import emoji
from discord.ext import commands, tasks
from utils import Gunibot, MyContext
import re


class Giveaways(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.config_options = ["giveaways_emojis"]
        self.internal_task.start()

        bot.get_command("config").add_command(self.giveaways_emojis)

    @commands.command(name="giveaways_emojis")
    async def giveaways_emojis(
        self, ctx: MyContext, emojis: commands.Greedy[Union[discord.Emoji, str]]
    ):
        """Set a list of usable emojis for giveaways
        Only these emojis will be usable to participate in a giveaway
        If no emoji is specified, every emoji will be usable"""
        # check if every emoji is valid
        emojis = [
            x for x in emojis if isinstance(x, discord.Emoji) or emoji.is_emoji(x)
        ]
        # if one or more emojis were invalid (couldn't be converted)
        if len(ctx.args[2]) != len(emojis):
            await ctx.send(await self.bot._(ctx.guild.id, "sconfig.invalid-emoji"))
            return
        # if user didn't specify any emoji
        if len(emojis) == 0:
            emojis = None
        # convert discord emojis to IDs if needed
        emojis = [str(x.id) if isinstance(x, discord.Emoji) else x for x in emojis]
        # save result
        await ctx.send(
            await self.bot.sconfig.edit_config(ctx.guild.id, "giveaways_emojis", emojis)
        )

    def db_add_giveaway(
        self,
        channel: discord.TextChannel,
        name: str,
        message: int,
        max_entries: int,
        ends_at: datetime.datetime = None,
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
            dumps(list()),
        )
        query = "INSERT INTO giveaways (guild, channel, name, max_entries, ends_at, message, users) VALUES (?, ?, ?, ?, ?, ?, ?)"
        rowid: int = self.bot.db_query(query, data)
        return rowid

    def db_get_giveaways(self, guildID: int) -> List[dict]:
        """
        Get giveaways attached to a server
        guildID: the guild (server) ID
        Returns: a list of dicts containing the giveaways info
        """
        query = "SELECT rowid, * FROM giveaways WHERE guild=?"
        liste = self.bot.db_query(query, (guildID,))
        res = list(map(dict, liste))
        for r in res:
            r["users"] = loads(r["users"])
            r["ends_at"] = datetime.datetime.strptime(r["ends_at"], "%Y-%m-%d %H:%M:%S")
        return res

    def db_get_expired_giveaways(self) -> List[dict]:
        """
        Get every running giveaway
        Returns: a list of dicts containing the giveaways info
        """
        query = "SELECT rowid, * FROM giveaways WHERE ends_at <= ? AND running = 1"
        liste = self.bot.db_query(query, (datetime.datetime.now(),))
        res = list(map(dict, liste))
        for r in res:
            r["users"] = loads(r["users"])
            r["ends_at"] = datetime.datetime.strptime(r["ends_at"], "%Y-%m-%d %H:%M:%S")
        return res

    def db_get_users(self, rowID: int) -> List[int]:
        """
        Get the users participating into a giveaway via command
        rowID: the ID of the giveaway to edit
        Returns: list of users IDs
        """
        query = "SELECT users FROM giveaways WHERE rowid=?"
        res = self.bot.db_query(query, (rowID,))
        if len(res) == 0:
            return None
        return loads(res[0]["users"])

    def db_edit_participant(self, rowID: int, userID: int, add: bool = True) -> bool:
        """
        Add a participant to a giveaway
        rowID: the ID of the giveaway to edit
        userID: the participant ID
        add: if we should add or remove the user
        Returns: if the operation succeed
        """
        current_participants = self.db_get_users(rowID)
        if current_participants is None:
            # means that the giveaway doesn't exist
            return False
        if add:
            if userID in current_participants:
                # user was already participating
                return
            current_participants = dumps(current_participants + [userID])
        else:
            try:
                current_participants.remove(userID)
            except ValueError:
                # user was not participating
                return
            current_participants = dumps(current_participants)
        query = "UPDATE giveaways SET users=? WHERE rowid=?"
        rowcount = self.bot.db_query(query, (rowID, userID), returnrowcount=True)
        return rowcount != 0

    def db_stop_giveaway(self, rowID: int) -> bool:
        """
        Stop a giveaway
        rowID: the ID of the giveaway to stop
        Returns: if the giveaway has successfully been stopped
        """
        query = "UPDATE giveaways SET running=0 WHERE rowid=?"
        rowcount = self.bot.db_query(query, (rowID,), returnrowcount=True)
        return rowcount == 1

    def db_delete_giveaway(self, rowID: int) -> bool:
        """
        Delete a giveaway from the database
        rowID: the ID of the giveaway to delete
        Returns: if the giveaway has successfully been deleted
        """
        query = "DELETE FROM giveaways WHERE rowid=?"
        rowcount = self.bot.db_query(query, (rowID,), returnrowcount=True)
        return rowcount == 1

    async def get_allowed_emojis(self, guildID: int) -> List[Union[discord.Emoji, str]]:
        """Get a list of allowed emojis for a specific guild"""
        value = self.bot.server_configs[guildID]["giveaways_emojis"]
        if value is None:
            return None

        def emojis_convert(
            s_emoji: str, bot_emojis: List[discord.Emoji]
        ) -> Union[str, discord.Emoji]:
            if s_emoji.isnumeric():
                d_em = discord.utils.get(bot_emojis, id=int(s_emoji))
                if d_em is not None:
                    return d_em
            return emoji.emojize(s_emoji, language="alias")

        value = [value] if isinstance(value, str) else value
        result = list(filter(None, [emojis_convert(x, self.bot.emojis) for x in value]))
        if len(result) >= 0:
            return result
        return None

    @commands.group(aliases=["gaw", "giveaways"])
    async def giveaway(self, ctx: MyContext):
        """Start or stop giveaways."""
        if ctx.subcommand_passed is None:
            await ctx.send_help("giveaways")

    @giveaway.command()
    @commands.check(checks.is_admin)
    async def start(self, ctx: MyContext, *, settings: str):
        """Start a giveaway
        Usage"
        [p]giveaway start name: <Giveaway name>; duration: <Time duration>; entries: [winners count]; channel: [channel mention]
        Giveaway name is mandatory.
        Duration is mandatory.
        Winners count is optional (default 1).
        Channel is optional (default current channel).

        Example:
        [p]giveaway start name: Minecraft account; duration: 3d;
        [p]giveaway start name: Minecraft account; duration: 2h; channel: #announcements
        [p]giveaway start name: Minecraft account; duration: 5h 3min; entries: 5"""
        i_settings = settings.split("; ")
        existing_giveaways = self.db_get_giveaways(ctx.guild.id)
        existing_giveaways = [x["name"] for x in existing_giveaways]

        # Setting all of the settings.
        settings = {"name": "", "duration": -1, "channel": ctx.channel, "entries": 1}
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
                    settings["name"] = setting[6:].strip()
            elif setting.startswith("entries: "):
                entries = setting.replace("entries: ", "").strip()
                if (not entries.isnumeric()) or (entries == "0"):
                    await ctx.send(
                        await self.bot._(
                            ctx.guild.id, "giveaways.creation.invalid-winners"
                        )
                    )
                    return
                settings["entries"] = int(entries)
            elif setting.startswith("duration: "):
                total = 0
                for elem in setting[10:].split():
                    total += await args.tempdelta().convert(ctx, elem)
                if total > 0:
                    settings["duration"] = total
            elif setting.startswith("channel: "):
                try:
                    channel = await commands.TextChannelConverter().convert(
                        ctx, setting.replace("channel: ", "")
                    )
                except:
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
                settings["channel"] = channel
        # Checking if mandatory settings are there.
        if settings["name"] == "":
            await ctx.send(
                await self.bot._(ctx.guild.id, "giveaways.creation.empty-name")
            )
            return
        if settings["duration"] == -1:
            await ctx.send(
                await self.bot._(ctx.guild.id, "giveaways.creation.empty-duration")
            )
            return
        settings["ends_at"] = datetime.datetime.fromtimestamp(
            round(time.time()) + settings["duration"]
        )
        # If the channel is too big, bugs will for sure happen, so we abort
        if len(settings["channel"].members) > 10000:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.too-many-members"))
            return
        # Send embed now
        try:
            title = await self.bot._(ctx.guild.id, "giveaways.embed.title")
            ends_at = await self.bot._(ctx.guild.id, "giveaways.embed.ends-at")
            emb = discord.Embed(
                title=title,
                description=settings["name"],
                timestamp=datetime.datetime.utcnow()
                + datetime.timedelta(seconds=settings["duration"]),
                color=discord.Colour.random(),
            ).set_footer(text=ends_at)
            msg: discord.Message = await settings["channel"].send(embed=emb)
            settings["message"] = msg.id
        except discord.HTTPException as e:
            await self.bot.get_cog("Errors").on_error(e, ctx)  # send error logs
            await ctx.send(
                await self.bot._(
                    ctx.guild.id,
                    "giveaways.creation.httpexception",
                    channe=settings["channel"].mention,
                )
            )
            return
        # Save settings in database
        rowid = self.db_add_giveaway(
            settings["channel"],
            settings["name"],
            settings["message"],
            settings["entries"],
            settings["ends_at"],
        )
        if rowid:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id,
                    "giveaways.creation.success",
                    name=settings["name"],
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
                for emoji in allowed_emojis:
                    try:
                        await msg.add_reaction(emoji)
                    except discord.NotFound:
                        pass
            except discord.Forbidden:
                pass

    @giveaway.command()
    @commands.check(checks.is_admin)
    async def stop(self, ctx: MyContext, *, giveaway: str):
        """Stops a giveaway early so you can pick a winner
        Example:
        [p]giveaway stop Minecraft account"""
        giveaways = self.db_get_giveaways(ctx.guild.id)
        if len(giveaways) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.no-giveaway"))
            return
        giveaway = [
            x for x in giveaways if x["name"] == giveaway or str(x["rowid"]) == giveaway
        ]
        if len(giveaway) == 0:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "giveaways.unknown-giveaway", p=ctx.prefix
                )
            )
            return
        giveaway = giveaway[0]
        if not giveaway["running"]:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.already-stopped"))
            return
        self.db_stop_giveaway(giveaway["rowid"])
        await self.send_results(giveaway, await self.pick_winners(ctx.guild, giveaway))

    @giveaway.command()
    @commands.check(checks.is_admin)
    async def delete(self, ctx: MyContext, *, giveaway: str):
        """
        Delete a giveaway from the database
        """
        giveaways = self.db_get_giveaways(ctx.guild.id)
        if len(giveaways) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.no-giveaway"))
            return
        giveaway = [
            x for x in giveaways if x["name"] == giveaway or str(x["rowid"]) == giveaway
        ]
        if len(giveaway) == 0:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "giveaways.unknown-giveaway", p=ctx.prefix
                )
            )
            return
        giveaway = giveaway[0]
        if self.db_delete_giveaway(giveaway["rowid"]):
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.success-deleted"))
        else:
            await ctx.send(
                await self.bot._(ctx.guild.id, "giveaways.something-went-wrong")
            )

    @giveaway.command()
    @commands.check(checks.is_admin)
    async def pick(self, ctx: MyContext, *, giveaway: str):
        """Picks winners for the giveaway, which usually should be 1
        Example:
        [p]giveaway pick Minecraft account (This will pick winners from all the people who entered the Minecraft account giveaway)"""
        giveaways = self.db_get_giveaways(ctx.guild.id)
        if len(giveaways) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.no-giveaway"))
            return
        giveaway = [
            x for x in giveaways if x["name"] == giveaway or str(x["rowid"]) == giveaway
        ]
        if len(giveaway) == 0:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "giveaways.unknown-giveaway", p=ctx.prefix
                )
            )
            return
        giveaway = giveaway[0]
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
                w = discord.utils.get(ctx.guild.members, id=random.choice(users))
                if w != None:
                    winners.append(w.mention)
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

    @giveaway.command()
    @commands.cooldown(2, 40, commands.BucketType.user)
    async def enter(self, ctx: MyContext, *, giveaway: str):
        """Enter a giveaway.
        Example:
        [p]giveaway enter Minecraft account"""
        if ctx.author.bot:
            await ctx.send("Les bots ne peuvent pas participer à un giveaway !")
            return
        author = ctx.message.author

        giveaways = self.db_get_giveaways(ctx.guild.id)
        if len(giveaways) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.no-giveaway"))
            return
        giveaways = [
            x for x in giveaways if x["name"] == giveaway or str(x["rowid"]) == giveaway
        ]
        if len(giveaways) == 0:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "giveaways.unknown-giveaway", p=ctx.prefix
                )
            )
            return
        ga = giveaways[0]
        if author.id in ga["users"]:
            await ctx.send(
                await self.bot._(ctx.guild.id, "giveaways.already-participant")
            )
        elif not ga["running"]:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.been-stopped"))
        else:
            if self.db_edit_participant(ga["rowid"], author.id):
                await ctx.send(
                    await self.bot._(
                        ctx.guild.id, "giveaways.subscribed", name=ga["name"]
                    )
                )
            else:
                await ctx.send(
                    await self.bot._(ctx.guild.id, "giveaways.something-went-wrong")
                )

    @giveaway.command()
    @commands.cooldown(2, 40, commands.BucketType.user)
    async def leave(self, ctx: MyContext, *, giveaway: str):
        """Leave a giveaway.
        Example:
        [p]giveaway leave Minecraft account"""
        if ctx.author.bot:
            await ctx.send("Les bots ne peuvent pas participer à un giveaway !")
            return
        author = ctx.message.author

        giveaways = self.db_get_giveaways(ctx.guild.id)
        if len(giveaways) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.no-giveaway"))
            return
        giveaways = [
            x for x in giveaways if x["name"] == giveaway or str(x["rowid"]) == giveaway
        ]
        if len(giveaways) == 0:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "giveaways.unknown-giveaway", p=ctx.prefix
                )
            )
            return
        ga = giveaways[0]
        if author.id not in ga["users"]:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.already-left"))
        elif not ga["running"]:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.been-stopped"))
        else:
            if self.db_edit_participant(ga["rowid"], author.id, add=False):
                await ctx.send(
                    await self.bot._(
                        ctx.guild.id, "giveaways.success-left", name=ga["name"]
                    )
                )
            else:
                await ctx.send(
                    await self.bot._(ctx.guild.id, "giveaways.something-went-wrong")
                )

    @giveaway.command()
    async def list(self, ctx: MyContext):
        """Lists all giveaways running in this server"""
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

    @giveaway.command()
    async def info(self, ctx: MyContext, *, giveaway: str):
        """Get information for a giveaway
        Example:
        [p]giveaway info Minecraft account"""
        giveaways = self.db_get_giveaways(ctx.guild.id)
        if len(giveaways) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "giveaways.no-giveaway"))
            return
        giveaway = [
            x for x in giveaways if x["name"] == giveaway or str(x["rowid"]) == giveaway
        ]
        if len(giveaway) == 0:
            await ctx.send(
                await self.bot._(
                    ctx.guild.id, "giveaways.unknown-giveaway", p=ctx.prefix
                )
            )
            return
        giveaway = giveaway[0]
        allowed_reactions = await self.get_allowed_emojis(ctx.guild.id)
        entries = len(
            set(giveaway["users"])
            | await self.get_users(
                giveaway["channel"], giveaway["message"], allowed_reactions
            )
        )
        d1, d2 = datetime.datetime.now(), giveaway["ends_at"]
        if d1 < d2:
            time_left = await self.bot.get_cog("TimeCog").time_delta(
                d2, d1, "fr", precision=0
            )
        elif d1 == d2:
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

    def cog_unload(self):
        self.internal_task.cancel()

    @tasks.loop(seconds=2.0)
    async def internal_task(self):
        for giveaway in self.db_get_expired_giveaways():
            if giveaway["running"]:
                try:
                    serv = self.bot.get_guild(giveaway["guild"])
                    winners = await self.pick_winners(serv, giveaway)
                    await self.send_results(giveaway, winners)
                    self.db_stop_giveaway(giveaway["rowid"])
                except Exception as e:
                    await self.bot.get_cog("Errors").on_error(e)
                    self.db_stop_giveaway(giveaway["rowid"])

    async def get_users(
        self,
        channel: int,
        message: int,
        allowed_reactions: Optional[set[Union[discord.Emoji, str]]],
    ):
        """Get users who reacted to a message"""
        channel: discord.TextChannel = self.bot.get_channel(channel)
        if channel is None:
            return set()
        message: discord.Message = await channel.fetch_message(message)
        if message is None or message.author != self.bot.user:
            return set()
        users = set()
        for react in message.reactions:
            if allowed_reactions is None or react.emoji in allowed_reactions:
                async for user in react.users():
                    if not user.bot:
                        users.add(user.id)
        return users

    async def edit_embed(
        self, channel: discord.TextChannel, message: int, winners: List[discord.Member]
    ) -> int:
        """Edit the embed to display results
        Returns the embed color if the embed was found, None else"""
        message: discord.Message = await channel.fetch_message(message)
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
        return emb.color

    async def pick_winners(
        self, guild: discord.Guild, giveaway: dict
    ) -> List[discord.Member]:
        """Select the winner of a giveaway, from both participants using the command and using the message reactions
        Returns a list of members"""
        allowed_reactions = await self.get_allowed_emojis(guild.id)
        users = set(giveaway["users"]) | await self.get_users(
            giveaway["channel"], giveaway["message"], allowed_reactions
        )
        if len(users) == 0:
            return list()
        else:
            amount = min(giveaway["max_entries"], len(users))
            winners = list()
            trials = 0
            users = list(users)
            while len(winners) < amount and trials < 20:
                w = discord.utils.get(guild.members, id=random.choice(users))
                if w != None:
                    winners.append(w)
                else:
                    trials += 1
        return winners

    async def send_results(self, giveaway: dict, winners: List[discord.Member]):
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
        desc = "{}: {} \n\n{}".format(
            await self.bot._(channel, "giveaways.embed.price"), giveaway["name"], win
        )
        emb = discord.Embed(
            title="Giveaway is over!", description=desc, color=emb_color
        )
        await channel.send(embed=emb)
        self.db_delete_giveaway(giveaway["rowid"])


config = {}
async def setup(bot:Gunibot=None, plugin_config:dict=None):
    if bot is not None:
        await bot.add_cog(Giveaways(bot), icon="🎁")
    if plugin_config is not None:
        global config
        config.update(plugin_config)
