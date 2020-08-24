import discord
import aiohttp
from discord.ext import commands
import checks


class VoiceChannels(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "voices"
        self.names = list()
        self.channels = dict()
        self.get_channels()
    
    def get_channels(self):
        c = self.bot.database.cursor()
        for row in c.execute('SELECT * FROM voices_chats'):
            self.channels[row[0]] = self.channels.get(row[0], list()) + [row[1]]
        c.close()
        # print(self.channels)
    
    def db_add_channel(self, channel: discord.VoiceChannel):
        c = self.bot.database.cursor()
        c.execute(f"INSERT INTO voices_chats (guild,channel) VALUES (?, ?)", (channel.guild.id, channel.id))
        c.close()
        self.channels[channel.guild.id] = self.channels.get(channel.guild.id, list()) + [channel.id]
    
    def db_delete_channel(self, channel: discord.VoiceChannel):
        c = self.bot.database.cursor()
        c.execute(f"DELETE FROM voices_chats WHERE guild=? AND channel=?", (channel.guild.id, channel.id))
        c.close()
        self.channels[channel.guild.id].remove(channel.id)


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
    
    async def create_channel(self, member: discord.Member, config: dict):
        """Create a new voice channel
        The member will get "Manage channel" permissions automatically"""
        if config["voices_category"] is None:  # si rien n'a été configuré
            return
        voice_category: discord.CategoryChannel = self.bot.get_channel(config["voices_category"])
        if not isinstance(voice_category, discord.CategoryChannel):
            return
        perms = voice_category.permissions_for(member.guild.me)
        if not (perms.manage_channels and perms.move_members): # S'il manque des perms au bot: abort
            return
        p = len(voice_category.channels)
        over = { member: discord.PermissionOverwrite(manage_channels=True) }
        new_channel = await voice_category.create_voice_channel(name=await self.get_names(), position=p, overwrites=over)
        await member.move_to(new_channel)
        self.db_add_channel(new_channel)
    
    async def delete_channel(self, channel: discord.VoiceChannel):
        """Delete an unusued channel if no one is in"""
        if len(channel.members) == 0 and channel.permissions_for(channel.guild.me).manage_channels:
            await channel.delete(reason="Unusued")
            self.db_delete_channel(channel)

    async def get_names(self):
        if len(self.names) != 0:
            return self.names.pop()
        async with aiohttp.ClientSession() as session:
            h = {'X-Api-Key': self.bot.config['random_api_token']}
            async with session.get('https://randommer.io/api/Name?nameType=surname&quantity=20', headers=h) as resp:
                self.names = await resp.json()
        return self.names.pop()


def setup(bot):
    bot.add_cog(VoiceChannels(bot))
