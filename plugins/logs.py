import discord
from discord.ext import commands
import checks


class Logs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.file = "logs"
    
    async def has_logs(self, guild) -> bool:
        """Check if a Guild has a valid logs channel"""
        if guild is None: return False
        config = self.bot.server_configs[guild.id]
        logs_channel: discord.TextChannel = guild.get_channel(config["logs_channel"])
        if not isinstance(logs_channel, discord.TextChannel): return False
        p = logs_channel.permissions_for(guild.me)
        return p.read_messages and p.send_messages and p.embed_links

    async def send_embed(self, guild, embed: discord.Embed):
        """Send the embed in a logs channel"""
        if guild is None: return
        config = self.bot.server_configs[guild.id]
        logs_channel: discord.TextChannel = guild.get_channel(config["logs_channel"])
        if not isinstance(logs_channel, discord.TextChannel): return
        await logs_channel.send(embed=embed)

    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_message_delete"
        if message.author.bot or (not await self.has_logs(message.guild)): return
        embed = discord.Embed(
            timestamp=message.created_at,
            description=f"Un message de {message.author.mention} ** a été supprimé** dans {message.channel.mention}",
            colour=discord.Colour.red()
        )
        embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
        embed.set_footer(text=f"Author ID:{message.author.id} • Message ID: {message.id}")
        embed.add_field(name="Contenu", value=message.content)
        await self.send_embed(message.guild, embed)
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_message_edit"
        if before.author.bot or (not await self.has_logs(before.guild)): return
        embed = discord.Embed(
            timestamp=after.created_at,
            description=f"Un message de {before.author.mention} **a été édité** dans {before.channel.mention}.",
            colour=discord.Colour(0x00FF00)
        )
        embed.set_author(name=str(before.author), icon_url=before.author.avatar_url)
        embed.set_footer(text=f"Author ID:{before.author.id} • Message ID: {before.id}")
        embed.add_field(name='Avant', value=before.content, inline=False)
        embed.add_field(name="Après", value=after.content, inline=False)
        await self.send_embed(before.guild, embed)
    
    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_raw_bulk_message_delete"
        guild = self.bot.get_guild(payload.guild_id)
        if not await self.has_logs(guild): return
        embed = discord.Embed(
            timestamp=message.created_at,
            description=f"{len(payload.message_ids)} messages **ont été supprimés** dans <#{payload.channel_id}>",
            colour=discord.Colour.red()
        )
        await self.send_embed(guild, embed)

def setup(bot):
    bot.add_cog(Logs(bot))
