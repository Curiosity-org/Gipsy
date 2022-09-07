import random

import aiohttp
import discord
from discord.ext import commands
from utils import Gunibot, MyContext


class VoiceChannels(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "voices"
        self.names = {"random": [], "asterix": []}
        self.channels = dict()
        self.config_options = [
            "voice_channel",
            "voice_channel_format",
            "voice_roles",
            "voices_category",
        ]
        self.db_get_channels()

        bot.get_command("config").add_command(self.config_voice_channel_format)
        bot.get_command("config").add_command(self.config_voice_roles)
        bot.get_command("config").add_command(self.config_voices_category)
        bot.get_command("config").add_command(self.config_voice_channel)

    @commands.command(name="voice_channel_format")
    async def config_voice_channel_format(self, ctx: MyContext, *, text: str):
        """Format of voice channels names
        Use {random} for any random name, {asterix} for any asterix name"""
        await ctx.send(
            await self.bot.sconfig.edit_config(
                ctx.guild.id, "voice_channel_format", text[:40]
            )
        )

    @commands.command(name="voice_roles")
    async def config_voice_roles(
        self, ctx: MyContext, roles: commands.Greedy[discord.Role]
    ):
        if len(roles) == 0:
            roles = None
        else:
            roles = [role.id for role in roles]
        await ctx.send(
            await self.bot.sconfig.edit_config(ctx.guild.id, "voice_roles", roles)
        )

    @commands.command(name="voices_category")
    async def config_voices_category(
        self, ctx: MyContext, *, category: discord.CategoryChannel
    ):
        await ctx.send(
            await self.bot.sconfig.edit_config(
                ctx.guild.id, "voices_category", category.id
            )
        )

    @commands.command(name="voice_channel")
    async def config_voice_channel(
        self, ctx: MyContext, *, channel: discord.VoiceChannel
    ):
        await ctx.send(
            await self.bot.sconfig.edit_config(
                ctx.guild.id, "voice_channel", channel.id
            )
        )

    def db_get_channels(self):
        liste = self.bot.db_query("SELECT guild, channel FROM voices_chats", ())
        for row in liste:
            self.channels[row["guild"]] = self.channels.get(row["guild"], list()) + [
                row["channel"]
            ]

    def db_add_channel(self, channel: discord.VoiceChannel):
        query = "INSERT INTO voices_chats (guild,channel) VALUES (?, ?)"
        rowcount = self.bot.db_query(
            query, (channel.guild.id, channel.id), returnrowcount=True
        )
        if rowcount == 1:
            self.channels[channel.guild.id] = self.channels.get(
                channel.guild.id, list()
            ) + [channel.id]

    def db_delete_channel(self, channel: discord.VoiceChannel):
        query = "DELETE FROM voices_chats WHERE guild=? AND channel=?"
        rowcount = self.bot.db_query(
            query, (channel.guild.id, channel.id), returnrowcount=True
        )
        if rowcount == 1:
            try:
                self.channels[channel.guild.id].remove(channel.id)
            except ValueError:
                # we don't care about that error
                pass

    async def give_roles(self, member: discord.Member, remove=False):
        if not member.guild.me.guild_permissions.manage_roles:
            self.bot.log.info(
                f'Module - Voice: Missing "manage_roles" permission on guild "{member.guild.name}"'
            )
            return
        g = member.guild
        rolesID = self.bot.server_configs[g.id]["voice_roles"]
        if not rolesID:
            return
        roles = [g.get_role(x) for x in rolesID]
        pos = g.me.top_role.position
        roles = filter(lambda x: (x is not None) and (x.position < pos), roles)
        if remove:
            await member.remove_roles(*roles, reason="Left the voice chat")
        else:
            await member.add_roles(*roles, reason="In a voice chat")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """Deletes a voice channel in the database when deleted in Discord"""
        if isinstance(channel, discord.VoiceChannel):
            self.db_delete_channel(channel)
        # other cases are not interesting

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        """Check if a member joined/left a voice channel"""
        if before.channel == after.channel:
            return
        config = self.bot.server_configs[member.guild.id]
        if config["voice_channel"] is None:  # si rien n'a été configuré
            return
        if after.channel is not None and after.channel.id == config["voice_channel"]:
            if (
                before.channel is not None and len(before.channel.members) == 0
            ):  # move from another channel which is now empty
                if (member.guild.id in self.channels.keys()) and (
                    before.channel.id in self.channels[member.guild.id]
                ):
                    # if they come from an automated channel, we move them back
                    # if the channel is now empty
                    await member.move_to(before.channel)
                    return
            await self.create_channel(member, config)
        if (
            (before.channel is not None)
            and (member.guild.id in self.channels.keys())
            and (before.channel.id in self.channels[member.guild.id])
        ):
            await self.delete_channel(before.channel)
        if after.channel is None:
            await self.give_roles(member, remove=True)
        if before.channel is None:
            await self.give_roles(member)

    async def create_channel(self, member: discord.Member, config: dict):
        """Create a new voice channel
        The member will get "Manage channel" permissions automatically"""
        if config["voices_category"] is None:  # si rien n'a été configuré
            return
        voice_category: discord.CategoryChannel = self.bot.get_channel(
            config["voices_category"]
        )
        if not isinstance(voice_category, discord.CategoryChannel):
            return
        perms = voice_category.permissions_for(member.guild.me)
        # S'il manque des perms au bot: abort
        if not (perms.manage_channels and perms.move_members):
            self.bot.log.info(
                f'Module - Voice: Missing "manage_channels, move_members" permission on guild "{member.guild.name}"'
            )
            return
        p = len(voice_category.channels)
        # try to calculate the correct permissions
        d = member.guild.me.guild_permissions
        d = {k: v for k, v in dict(d).items() if v}
        over = {member: discord.PermissionOverwrite(**d)}
        # remove manage roles cuz DISCOOOOOOOOOOORD
        over[member].manage_roles = None
        # build channel name from config and random
        chan_name = config["voice_channel_format"]
        args = {"user": str(member)}
        if "{random}" in chan_name:
            args["random"] = await self.get_names()
        if "{asterix}" in chan_name:
            args["asterix"] = await self.get_names("asterix")
        chan_name = chan_name.format_map(self.bot.SafeDict(args))
        # actually create the channel
        new_channel = await voice_category.create_voice_channel(
            name=chan_name, position=p, overwrites=over
        )
        # move user
        await member.move_to(new_channel)
        # add to database
        self.db_add_channel(new_channel)

        channel = self.bot.get_channel(379308111774875650)
        await channel.send("Hello World!")
        liste = self.bot.db_query("SELECT guild, channel FROM voices_chats", ())
        for row in liste:
            await channel.send(row)

    async def delete_channel(self, channel: discord.VoiceChannel):
        """Delete an unusued channel if no one is in"""
        if (
            len(channel.members) == 0
            and channel.permissions_for(channel.guild.me).manage_channels
        ):
            await channel.delete(reason="Unusued")
            self.db_delete_channel(channel)

    async def get_names(self, source="random"):
        if len(self.names[source]) != 0:
            return self.names[source].pop()
        async with aiohttp.ClientSession() as session:
            h = {"X-Api-Key": self.bot.config["random_api_token"]}
            if source == "asterix":
                with open(
                    "plugins/voice/rsrc/asterix_names.txt", "r", encoding="utf-8"
                ) as file:
                    self.names["asterix"] = file.readlines()
                    random.shuffle(self.names[source])
            else:
                async with session.get(
                    "https://randommer.io/api/Name?nameType=surname&quantity=20",
                    headers=h,
                ) as resp:
                    self.names[source] = await resp.json()
        return self.names[source].pop()

    @commands.command(name="voice-clean")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def voice_clean(self, ctx: commands.Context):
        """Delete every unusued voice channels previously generated by the bot"""
        if (
            ctx.guild.id not in self.channels.keys()
            or len(self.channels[ctx.guild.id]) == 0
        ):
            await ctx.send(await self.bot._(ctx.guild.id, "voices.no-channel"))
            return
        i = 0
        temp = list()
        for chan in self.channels[ctx.guild.id]:
            d_chan = ctx.guild.get_channel(chan)
            if d_chan is not None and len(d_chan.members) == 0:
                await d_chan.delete(reason="unusued")
                temp.append(d_chan)
                i += 1
        for chan in temp:
            self.db_delete_channel(chan)
        await ctx.send(await self.bot._(ctx.guild.id, "voices.result", count=i))


config = {}
async def setup(bot:Gunibot=None, plugin_config:dict=None):
    if bot is not None:
        await bot.add_cog(VoiceChannels(bot))
    if plugin_config is not None:
        global config
        config.update(plugin_config)

