import discord
from discord.ext import commands
import checks
import datetime

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
    
    def get_flags(self, guildID):
        f = self.bot.get_cog('ConfigCog').LogsFlags().intToFlags
        return f(self.bot.server_configs[guildID]['modlogs_flags'])


    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_message_delete"
        if message.author.bot or (not await self.has_logs(message.guild)): return
        if 'messages' not in self.get_flags(message.guild.id): return
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
        if 'messages' not in self.get_flags(before.guild.id): return
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
        if 'messages' not in self.get_flags(guild.id): return
        embed = discord.Embed(
            timestamp=message.created_at,
            description=f"{len(payload.message_ids)} messages **ont été supprimés** dans <#{payload.channel_id}>",
            colour=discord.Colour.red()
        )
        await self.send_embed(guild, embed)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_invite_create"
        if not await self.has_logs(invite.guild): return
        if 'invites' not in self.get_flags(invite.guild.id): return
        embed = discord.Embed(
            timestamp=invite.created_at,
            name="Invite",
            description=f"Invitation vers {invite.channel.mention}",
            colour=discord.Colour.green()
        )
        embed.set_author(name=f'{invite.inviter.name}#{invite.inviter.discriminator}',
                         icon_url=invite.inviter.avatar_url_as(static_format='jpg'))
        if invite.max_age == 0:
            embed.add_field(name="Durée", value="♾")
        else:
            embed.add_field(name="Durée", value=f"{datetime.timedelta(seconds=invite.max_age)}")
        embed.add_field(name="URL", value=invite.url)
        embed.add_field(name="Nombre max d'utilisations", value="♾" if invite.max_uses==0 else str(invite.max_uses))
        embed.set_footer(text=f"Author ID:{invite.inviter.id}")
        await self.send_embed(invite.guild, embed)

def setup(bot):
    bot.add_cog(Logs(bot))
