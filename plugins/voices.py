import discord
import aiohttp
import random
from discord.ext import commands
import checks


class VoiceChannels(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "voices"
        self.names = {'random': [], 'asterix': []}
        self.channels = dict()
        self.db_get_channels()

    def db_get_channels(self):
        c = self.bot.database.cursor()
        for row in c.execute('SELECT * FROM voices_chats'):
            self.channels[row[0]] = self.channels.get(
                row[0], list()) + [row[1]]
        c.close()

    def db_add_channel(self, channel: discord.VoiceChannel):
        c = self.bot.database.cursor()
        c.execute(f"INSERT INTO voices_chats (guild,channel) VALUES (?, ?)",
                  (channel.guild.id, channel.id))
        self.bot.database.commit()
        c.close()
        self.channels[channel.guild.id] = self.channels.get(
            channel.guild.id, list()) + [channel.id]

    def db_delete_channel(self, channel: discord.VoiceChannel):
        c = self.bot.database.cursor()
        c.execute(f"DELETE FROM voices_chats WHERE guild=? AND channel=?",
                  (channel.guild.id, channel.id))
        self.bot.database.commit()
        c.close()
        self.channels[channel.guild.id].remove(channel.id)

    async def give_roles(self, member: discord.Member, remove=False):
        if not member.guild.me.guild_permissions.manage_roles:
            return
        g = member.guild
        rolesID = self.bot.server_configs[g.id]['voice_roles']
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
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Check if a member joined/left a voice channel"""
        if before.channel == after.channel:
            return
        config = self.bot.server_configs[member.guild.id]
        if config["voice_channel"] is None:  # si rien n'a été configuré
            return
        if after.channel is not None and after.channel.id == config["voice_channel"]:
            await self.create_channel(member, config)
        if (before.channel is not None) and (member.guild.id in self.channels.keys()) and (before.channel.id in self.channels[member.guild.id]):
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
            config["voices_category"])
        if not isinstance(voice_category, discord.CategoryChannel):
            return
        perms = voice_category.permissions_for(member.guild.me)
        # S'il manque des perms au bot: abort
        if not (perms.manage_channels and perms.move_members):
            return
        p = len(voice_category.channels)
        d = dict(discord.Permissions.all())
        over = {member: discord.PermissionOverwrite(**d)}
        chan_name = config['voice_channel_format']
        args = {'user': str(member)}
        if "{random}" in chan_name:
            args['random'] = await self.get_names()
        if "{asterix}" in chan_name:
            args['asterix'] = await self.get_names('asterix')
        chan_name = chan_name.format_map(self.bot.SafeDict(args))
        new_channel = await voice_category.create_voice_channel(name=chan_name, position=p, overwrites=over)
        await member.move_to(new_channel)
        self.db_add_channel(new_channel)

    async def delete_channel(self, channel: discord.VoiceChannel):
        """Delete an unusued channel if no one is in"""
        if len(channel.members) == 0 and channel.permissions_for(channel.guild.me).manage_channels:
            await channel.delete(reason="Unusued")
            self.db_delete_channel(channel)

    async def get_names(self, source='random'):
        if len(self.names[source]) != 0:
            return self.names[source].pop()
        async with aiohttp.ClientSession() as session:
            h = {'X-Api-Key': self.bot.config['random_api_token']}
            if source == 'asterix':
                async with session.get('https://raw.githubusercontent.com/Gunivers/Gunibot/master/src/main/resources/other/bdd%20name', headers=h) as resp:
                    self.names[source] = (await resp.text()).split('\n')
                    random.shuffle(self.names[source])
            else:
                async with session.get('https://randommer.io/api/Name?nameType=surname&quantity=20', headers=h) as resp:
                    self.names[source] = await resp.json()
        return self.names[source].pop()

    @commands.command(name="voice-clean")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def voice_clean(self, ctx: commands.Context):
        """Delete every unusued voice channels previously generated by the bot"""
        if not ctx.guild.id in self.channels.keys() or len(self.channels[ctx.guild.id]) == 0:
            await ctx.send("There's no generated voice channel here")
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
        await ctx.send(f"Deleted {i} channel" + ('' if i == 1 else 's'))


def setup(bot):
    bot.add_cog(VoiceChannels(bot))
