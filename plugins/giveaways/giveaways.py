"""giveways
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import datetime
import random
from marshal import dumps, loads
from typing import Any, Optional, Sequence, Union

import discord
from discord import app_commands
from discord.ext import commands, tasks

from bot import args
from utils import Gunibot
from core import setup_logger

from .src.view import GiveawayView

class Giveaways(commands.Cog):
    "Manage giveaways in your server"

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.embed_color = 0x9933ff
        self.logger = setup_logger('giveways')

    async def cog_load(self):
        self.internal_task.start() # pylint: disable=no-member

    async def cog_unload(self):
        self.internal_task.cancel() # pylint: disable=no-member

    @tasks.loop(seconds=5)
    async def internal_task(self):
        "Stop expired giveaways"
        for giveaway in self.db_get_expired_giveaways():
            serv = self.bot.get_guild(giveaway["guild"])
            if serv is None:
                continue
            winners = await self.pick_winners(serv, giveaway)
            await self.send_results(giveaway, winners)
            self.db_delete_giveaway(giveaway["rowid"])

    def db_add_giveaway(
        self,
        channel: discord.TextChannel,
        name: str,
        message_id: int,
        max_entries: int,
        ends_at: datetime.datetime,
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
            message_id,
            dumps([]),
        )
        query = "INSERT INTO `giveaways` \
            (guild, channel, name, max_entries, ends_at, message, users) \
            VALUES (?, ?, ?, ?, ?, ?, ?)"
        rowid: int = self.bot.db_query(query, data)
        return rowid

    def db_get_giveaways(self, guild_id: int) -> list[dict]:
        """
        Get giveaways attached to a server
        guildID: the guild (server) ID
        Returns: a list of dicts containing the giveaways info
        """
        query = "SELECT rowid, * FROM `giveaways` WHERE `guild` = ?"
        res: list[dict[str, Any]] = self.bot.db_query(query, (guild_id,))
        for data in res:
            data["users"] = loads(data["users"])
            data["ends_at"] = datetime.datetime.strptime(data["ends_at"], "%Y-%m-%d %H:%M:%S.%f")
        return res

    def db_get_giveaway(self, guild_id: int, giveaway_id: int) -> Optional[dict]:
        """
        Get a giveaway from its ID
        guildID: the guild (server) ID
        Returns: a list of dicts containing the giveaways info
        """
        query = "SELECT `rowid`, * FROM `giveaways` WHERE `guild` = ? AND `rowid` = ?"
        res: list[dict[str, Any]] = self.bot.db_query(query, (guild_id, giveaway_id))
        for data in res:
            data["users"] = loads(data["users"])
            data["ends_at"] = datetime.datetime.strptime(data["ends_at"], "%Y-%m-%d %H:%M:%S.%f")
        return res[0] if res else None

    def db_get_expired_giveaways(self) -> list[dict]:
        """
        Get every giveaway that should have ended
        Returns: a list of dicts containing the giveaways info
        """
        query = "SELECT `rowid`, * FROM `giveaways` WHERE `ends_at` <= ?"
        res: list[dict[str, Any]] = self.bot.db_query(query, (datetime.datetime.now(),))
        for data in res:
            data["users"] = loads(data["users"])
            data["ends_at"] = datetime.datetime.strptime(data["ends_at"], "%Y-%m-%d %H:%M:%S.%f")
        return res

    def db_get_users(self, giveaway_id: int) -> list[int] | None:
        """
        Get the users participating into a giveaway via command
        rowID: the ID of the giveaway to edit
        Returns: list of users IDs
        """
        query = "SELECT `users` FROM `giveaways` WHERE `rowid` = ?"
        res: list[dict[str, bytes]] = self.bot.db_query(query, (giveaway_id,))
        if len(res) == 0:
            return None
        return loads(res[0]["users"])

    def db_edit_participant(self, giveaway_id: int, user_id: int, add: bool = True) -> bool:
        """
        Add a participant to a giveaway
        rowID: the ID of the giveaway to edit
        userID: the participant ID
        add: if we should add or remove the user
        Returns: if the operation succeed
        """
        current_participants = self.db_get_users(giveaway_id)
        if current_participants is None:
            # means that the giveaway doesn't exist
            self.bot.log.warning(f"[gaw] Giveaway {giveaway_id} doesn't exist")
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
        query = "UPDATE `giveaways` SET `users`=? WHERE `rowid` = ?"
        rowcount = self.bot.db_query(query, (current_participants, giveaway_id),
                                     returnrowcount=True)
        return rowcount != 0

    def db_delete_giveaway(self, giveaway_id: int) -> bool:
        """
        Delete a giveaway from the database
        rowID: the ID of the giveaway to delete
        Returns: if the giveaway has successfully been deleted
        """
        query = "DELETE FROM giveaways WHERE `rowid` = ?"
        rowcount = self.bot.db_query(query, (giveaway_id,), returnrowcount=True)
        return rowcount == 1


    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Called when *any* interaction from the bot is created
        We use it to detect interactions with the Enter button of any giveaway"""
        if not interaction.guild:
            # DM: not interesting
            return
        if interaction.type != discord.InteractionType.component:
            # Not button: not interesting
            return
        if not interaction.data or not interaction.data.get("custom_id", '').startswith("gaw_"):
            # Not a giveaway: not interesting
            return
        await interaction.response.defer(ephemeral=True)
        await self.enter_giveaway(interaction)


    giveaway = app_commands.Group(
        name="giveaway",
        description="Create and manage giveaways on your server",
        default_permissions=discord.Permissions(manage_guild=True),
    )

    @giveaway.command(name="start")
    async def gw_start(self, interaction: discord.Interaction,
                       name: app_commands.Range[str, 1, 60],
                       duration: str,
                       entries: app_commands.Range[int, 1]=1,
                       channel: Optional[discord.TextChannel]=None):
        """Start a giveaway

        Usage:
        /giveaway start
                    name: The public giveaway name
                    duration: How long the giveaway should last
                    entries: How many winners there should be (default 1)
                    channel: In which channel the giveaway should be sent (default current channel)
        Giveaway name is mandatory.
        Duration is mandatory.
        Winners count is optional (default 1).
        Channel is optional (default current channel).

        Example:
        /giveaway start name: Minecraft account duration: 3d
        /giveaway start name: Minecraft account duration: 2h channel: #announcements
        /giveaway start name: Minecraft account duration: 5h 3min entries: 5"""
        existing_giveaways: set[str] = {
            g["name"]
            for g in self.db_get_giveaways(interaction.guild.id)
        }
        await interaction.response.defer()

        # check name validity
        if name in existing_giveaways:
            await interaction.followup.send(
                await self.bot._(interaction.guild.id, "giveaways.creation.invalid-name"),
                ephemeral=True
            )
            return
        # check duration validity
        parsed_duration = 0
        for elem in duration.split():
            parsed_duration += await args.tempdelta().convert(interaction, elem)
        if parsed_duration == 0:
            await interaction.followup.send(
                await self.bot._(interaction.guild.id, "giveaways.creation.invalid-duration"),
                ephemeral=True
            )
            return
        end_date = datetime.datetime.now() + datetime.timedelta(seconds=parsed_duration)
        # check channel validity
        parsed_channel: discord.abc.MessageableChannel = channel or interaction.channel
        perms = parsed_channel.permissions_for(interaction.guild.me)
        if not (perms.send_messages or perms.embed_links):
            await interaction.followup.send(
                await self.bot._(
                    interaction.guild.id, "giveaways.creation.invalid-perms"
                ),
                ephemeral=True
            )
            return

        # Send embed now
        try:
            title = await self.bot._(interaction.guild.id, "giveaways.embed.title")
            emb = discord.Embed(
                title=title,
                description=name,
                timestamp=end_date.astimezone(datetime.timezone.utc),
                color=discord.Colour.random(),
            )
            msg: discord.Message = await parsed_channel.send(embed=emb)
        except discord.HTTPException as err:
            self.bot.dispatch("error", err, interaction)  # send error logs
            await interaction.followup.send(
                await self.bot._(
                    interaction.guild.id,
                    "giveaways.creation.httpexception",
                    channel=parsed_channel.mention,
                )
            )
            return
        # Save settings in database
        rowid = self.db_add_giveaway(
            parsed_channel,
            name,
            msg.id,
            entries,
            end_date,
        )
        if rowid:
            await interaction.followup.send(
                await self.bot._(
                    interaction.guild.id,
                    "giveaways.creation.success",
                    name=name,
                    id=rowid,
                )
            )
            view = GiveawayView(
                self.bot,
                await self.bot._(interaction.guild.id, "giveaways.view.enter_btn"),
                custom_id=f"gaw_{rowid}",
            )
            ends_at = await self.bot._(interaction.guild.id, "giveaways.embed.ends-at")
            id_footer = await self.bot._(interaction.guild.id, "giveaways.embed.id-footer",
                                         id=rowid)
            emb.set_footer(text=id_footer + ' | ' + ends_at)
            await msg.edit(view=view)
        else:
            await interaction.followup.send(
                await self.bot._(interaction.guild.id, "giveaways.something-went-wrong")
            )

    @giveaway.command(name="stop")
    async def gw_stop(self, interaction: discord.Interaction, *, giveaway_name: str):
        """Stops a giveaway early so you can pick a winner
        
        Example:
        /giveaway stop Minecraft account"""
        giveaways = self.db_get_giveaways(interaction.guild_id)
        if len(giveaways) == 0:
            await interaction.response.send_message(
                await self.bot._(interaction.guild_id, "giveaways.no-giveaway")
            )
            return
        filtered_giveaway = [
            x
            for x in giveaways
            if x["name"].lower() == giveaway_name.lower() or str(x["rowid"]) == giveaway_name
        ]
        if len(filtered_giveaway) == 0:
            list_cmd = await self.bot.get_command_mention("giveaway list-giveaways")
            await interaction.response.send_message(
                await self.bot._(
                    interaction.guild_id, "giveaways.unknown-giveaway", list_cmd=list_cmd
                )
            )
            return
        giveaway = filtered_giveaway[0]
        await self.send_results(giveaway, await self.pick_winners(interaction.guild, giveaway))
        self.db_delete_giveaway(giveaway["rowid"])
        await interaction.response.send_message(
            await self.bot._(interaction.guild_id, "giveaways.success-stopped")
        )

    @giveaway.command(name="cancel")
    async def gw_cancel(self, interaction: discord.Interaction, *, giveaway_name: str):
        """
        Cancel a giveaway and remove it from the database
        """
        giveaways = self.db_get_giveaways(interaction.guild_id)
        if len(giveaways) == 0:
            await interaction.response.send_message(
                await self.bot._(interaction.guild_id, "giveaways.no-giveaway")
            )
            return
        filtered_giveaway = [
            x
            for x in giveaways
            if x["name"].lower() == giveaway_name.lower() or str(x["rowid"]) == giveaway_name
        ]
        if len(filtered_giveaway) == 0:
            list_cmd = await self.bot.get_command_mention("giveaway list-giveaways")
            await interaction.response.send_message(
                await self.bot._(
                    interaction.guild_id, "giveaways.unknown-giveaway", list_cmd=list_cmd
                )
            )
            return
        giveaway = filtered_giveaway[0]
        if self.db_delete_giveaway(giveaway["rowid"]):
            await interaction.response.send_message(
                await self.bot._(interaction.guild_id, "giveaways.success-cancelled")
            )
        else:
            await interaction.response.send_message(
                await self.bot._(interaction.guild_id, "giveaways.something-went-wrong")
            )

    @giveaway.command(name="list-giveaways")
    async def gw_list(self, interaction: discord.Interaction):
        """
        Lists all giveaways in this server
        """
        giveaways = self.db_get_giveaways(interaction.guild_id)
        if len(giveaways) == 0:
            await interaction.response.send_message(
                await self.bot._(interaction.guild_id, "giveaways.no-giveaway")
            )
            return
        title = await self.bot._(interaction.guild_id, "giveaways.list.title")
        text = "\n".join([
            await self.bot._(
                interaction.guild_id, "giveaways.list.row",
                id=gaw['rowid'], name=gaw['name'], count=len(gaw['users'])
            )
            for gaw in giveaways
        ])
        embed = discord.Embed(title=title, description=text, color=self.embed_color)
        await interaction.response.send_message(embed=embed)

    @giveaway.command(name="info")
    async def gw_info(self, interaction: discord.Interaction, giveaway_name: str):
        """Get information for a giveaway
        
        Example:
        /giveaway info Minecraft account"""
        giveaways = self.db_get_giveaways(interaction.guild_id)
        if len(giveaways) == 0:
            await interaction.response.send_message(
                await self.bot._(interaction.guild_id, "giveaways.no-giveaway")
            )
            return
        fileterd_giveaway = [
            x
            for x in giveaways
            if x["name"].lower() == giveaway_name.lower() or str(x["rowid"]) == giveaway_name
        ]
        if len(fileterd_giveaway) == 0:
            list_cmd = await self.bot.get_command_mention("giveaway list-giveaways")
            await interaction.response.send_message(
                await self.bot._(
                    interaction.guild_id, "giveaways.unknown-giveaway", list_cmd=list_cmd
                ),
                ephemeral=True
            )
            return
        giveaway = fileterd_giveaway[0]
        entries = len(set(giveaway["users"]))
        start, end = datetime.datetime.now(), giveaway["ends_at"]
        if start < end:
            time_left = await self.bot.get_cog("TimeCog").time_delta(
                end, start, "fr", precision=0
            )
        elif start == end:
            time_left = await self.bot._(interaction.guild_id, "giveaways.info.soon")
        else:
            time_left = await self.bot._(interaction.guild_id, "giveaways.info.ended")
        name = giveaway["name"]
        msg_url = f"https://discord.com/channels/{interaction.guild_id}/{giveaway['channel']}/{giveaway['message']}"
        txt = await self.bot._(
            interaction.guild_id,
            "giveaways.info.summary",
            name=name,
            time=time_left,
            nbr=entries,
            max_entries=giveaway["max_entries"],
            msg_url=msg_url,
        )
        embed = discord.Embed(
            title=await self.bot._(interaction.guild_id, "giveaways.info.title"),
            description=txt,
            color=self.embed_color,
        )
        await interaction.response.send_message(embed=embed)

    @gw_stop.autocomplete("giveaway_name")
    @gw_cancel.autocomplete("giveaway_name")
    @gw_info.autocomplete("giveaway_name")
    async def _giveaway_name_autocompletion(self, interaction: discord.Interaction, current: str):
        "Autocompletion to select a giveaway in an app command"
        current = current.lower()
        giveaways = self.db_get_giveaways(interaction.guild_id)
        filtered = sorted([
            (not x["name"].lower().startswith(current), x["name"], x["rowid"])
            for x in giveaways
            if current in x["name"].lower() or x["rowid"] == current
        ])
        return [
            app_commands.Choice(name=name, value=str(rowid))
            for _, name, rowid in filtered
        ]

    async def enter_giveaway(self, interaction: discord.Interaction):
        "Called when a user press the Enter button"
        # get back giveaway ID from custom button ID
        if not interaction.data or not interaction.data["custom_id"]:
            return
        if not (custom_id := interaction.data["custom_id"]).startswith("gaw_"):
            return
        giveaway_id = int(custom_id.replace("gaw_", "", 1))
        # check if giveaway exists
        giveaway = self.db_get_giveaway(interaction.guild_id, giveaway_id)
        if not giveaway:
            await interaction.followup.send(
                await self.bot._(interaction.guild_id, "giveaways.something-went-wrong"),
                ephemeral=True,
            )
            raise RuntimeError(f"Unable to find giveaway {giveaway_id}")
        # check if user is already participating
        if interaction.user.id in giveaway["users"]:
            await interaction.followup.send(
                await self.bot._(interaction.guild_id, "giveaways.already-participant"),
                ephemeral=True,
            )
            return
        # try to add user to giveaway
        if self.db_edit_participant(giveaway["rowid"], interaction.user.id, add=True):
            await interaction.followup.send(
                await self.bot._(
                    interaction.guild_id, "giveaways.subscribed", name=giveaway["name"]
                ),
                ephemeral=True,
            )
            return
        # adding failed
        await interaction.followup.send(
            await self.bot._(interaction.guild_id, "giveaways.something-went-wrong"),
            ephemeral=True,
        )
        raise RuntimeError(
            f"Something went wrong when adding a participant to giveaway {giveaway_id}"
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
        self, channel: discord.TextChannel, gaw_id: int, message_id: int,
        winners: list[discord.Member]
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
        ended_at = await self.bot._(channel, "giveaways.embed.ends-at")
        id_footer = await self.bot._(channel, "giveaways.embed.id-footer",
                                        id=gaw_id)
        emb.set_footer(text=id_footer + ' | ' + ended_at)
        if winners:
            winners_list = " ".join(x.mention for x in winners)
        else:
            winners_list = await self.bot._(channel, "giveaways.embed.winners", count=0)
        emb.add_field(
            name=await self.bot._(channel, "giveaways.embed.winners-count", count=len(winners)),
            value=winners_list,
            inline=False
        )
        await message.edit(embed=emb, view=None)
        return emb.color.value if emb.color else None

    async def pick_winners(
        self, guild: discord.Guild, giveaway: dict
    ) -> list[discord.Member]:
        """Select the winner of a giveaway, from both participants using the command and using the
        message reactions

        Returns a list of members
        """
        users = set(giveaway["users"])
        if len(users) == 0:
            return []
        amount = min(giveaway["max_entries"], len(users))
        winners = []
        trials = 0
        users = list(users)
        while len(winners) < amount and trials < 20:
            winner = discord.utils.get(guild.members, id=random.choice(users))
            if winner is not None:
                winners.append(winner)
                users.remove(winner.id)
            else:
                trials += 1
        return winners

    async def send_results(self, giveaway: dict, winners: list[discord.Member]):
        """Send the giveaway results in a new embed"""
        self.logger.info("Giveaway '%s' has stopped", giveaway['name'])
        channel: discord.TextChannel = self.bot.get_channel(giveaway["channel"])
        if channel is None:
            return None
        emb_color = await self.edit_embed(channel, giveaway["rowid"], giveaway["message"], winners)
        if emb_color is None:
            # old embed wasn't found, we select a new color
            emb_color = discord.Colour.random()
        win = await self.bot._(
            channel,
            "giveaways.embed.winners",
            count=len(winners),
            winner=" ".join([x.mention for x in winners]),
        )
        desc = giveaway["name"] + "\n\n" + win
        emb = discord.Embed(
            title="Giveaway is over!", description=desc, color=emb_color
        )
        await channel.send(embed=emb)


async def setup(bot: Gunibot | None = None):
    if bot is not None:
        await bot.add_cog(Giveaways(bot), icon="🎁")
