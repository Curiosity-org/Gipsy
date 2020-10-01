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
        if guild is None:
            return False
        config = self.bot.server_configs[guild.id]
        logs_channel: discord.TextChannel = guild.get_channel(
            config["logs_channel"])
        if not isinstance(logs_channel, discord.TextChannel):
            return False
        p = logs_channel.permissions_for(guild.me)
        return p.read_messages and p.send_messages and p.embed_links

    async def send_embed(self, guild, embed: discord.Embed):
        """Send the embed in a logs channel"""
        if guild is None:
            return
        config = self.bot.server_configs[guild.id]
        logs_channel: discord.TextChannel = guild.get_channel(
            config["logs_channel"])
        if not isinstance(logs_channel, discord.TextChannel):
            return
        await logs_channel.send(embed=embed)

    def get_flags(self, guildID):
        f = self.bot.get_cog('ConfigCog').LogsFlags().intToFlags
        return f(self.bot.server_configs[guildID]['modlogs_flags'])

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_message_delete"
        if message.author.bot or (not await self.has_logs(message.guild)):
            return
        if 'messages' not in self.get_flags(message.guild.id):
            return
        embed = discord.Embed(
            timestamp=message.created_at,
            title="Message supprimé",
            description=f"Un message de {message.author.mention} ** a été supprimé** dans {message.channel.mention}",
            colour=discord.Colour(13632027)
        )
        embed.set_author(name=str(message.author),
                         icon_url=message.author.avatar_url)
        embed.set_footer(
            text=f"Author ID: {message.author.id} • Message ID: {message.id}")
        embed.add_field(name="Contenu", value=message.content)
        await self.send_embed(message.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_message_edit"
        if before.author.bot or (not await self.has_logs(before.guild)):
            return
        if before.content == after.content:
            return  # when edition is only adding an embed, for example
        if 'messages' not in self.get_flags(before.guild.id):
            return
        embed = discord.Embed(
            timestamp=after.created_at,
            title="Message édité",
            description=f"Un message de {before.author.mention} **a été édité** dans {before.channel.mention}.",
            colour=discord.Colour(16294684)
        )
        embed.set_author(name=str(before.author),
                         icon_url=before.author.avatar_url)
        embed.set_footer(
            text=f"Author ID: {before.author.id} • Message ID: {before.id}")
        if len(before.content) > 1024:
            before.content = before.content[:1020] + '...'
        if len(after.content) > 1024:
            after.content = after.content[:1020] + '...'
        embed.add_field(name='Avant', value=before.content, inline=False)
        embed.add_field(name="Après", value=after.content, inline=False)
        await self.send_embed(before.guild, embed)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_raw_bulk_message_delete"
        guild = self.bot.get_guild(payload.guild_id)
        if not await self.has_logs(guild):
            return
        if 'messages' not in self.get_flags(guild.id):
            return
        embed = discord.Embed(
            timestamp=datetime.datetime.utcnow(),
            title="Messages supprimés",
            description=f"{len(payload.message_ids)} messages **ont été supprimés** dans <#{payload.channel_id}>",
            colour=discord.Colour.red()
        )
        await self.send_embed(guild, embed)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_invite_create"
        if not await self.has_logs(invite.guild):
            return
        if 'invites' not in self.get_flags(invite.guild.id):
            return
        embed = discord.Embed(
            timestamp=invite.created_at,
            title="Invitation créée",
            description=f"Invitation créée vers {invite.channel.mention}",
            colour=discord.Colour.green()
        )
        if invite.inviter: # sometimes Discord doesn't send that info
            embed.set_author(name=f'{invite.inviter.name}#{invite.inviter.discriminator}',
                             icon_url=invite.inviter.avatar_url_as(static_format='png'))
            embed.set_footer(text=f"Author ID: {invite.inviter.id}")
        if invite.max_age == 0:
            embed.add_field(name="Durée", value="♾")
        else:
            embed.add_field(
                name="Durée", value=f"{datetime.timedelta(seconds=invite.max_age)}")
        embed.add_field(name="URL", value=invite.url)
        embed.add_field(name="Nombre max d'utilisations",
                        value="♾" if invite.max_uses == 0 else str(invite.max_uses))
        await self.send_embed(invite.guild, embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_invite_delete"
        if not await self.has_logs(invite.guild):
            return
        if 'invites' not in self.get_flags(invite.guild.id):
            return
        embed = discord.Embed(
            title="Invitation supprimée",
            description=f"Invitation supprimée vers {invite.channel.mention}",
            colour=discord.Colour.green()
        )
        if invite.inviter:
            embed.set_author(name=f'{invite.inviter.name}#{invite.inviter.discriminator}',
                             icon_url=invite.inviter.avatar_url_as(static_format='png'))
            embed.set_footer(text=f"Author ID: {invite.inviter.id}")
        embed.add_field(name="URL", value=invite.url)
        await self.send_embed(invite.guild, embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_member_join"
        await self.on_member_join_remove(member, True)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_member_remove"
        await self.on_member_join_remove(member, False)

    async def on_member_join_remove(self, member: discord.Member, join: bool):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_invite_delete"
        if not await self.has_logs(member.guild):
            return
        if 'joins' not in self.get_flags(member.guild.id):
            return
        if join:
            embed = discord.Embed(
                title="Arrivée d'un membre",
                description=member.mention + " a rejoint votre serveur",
                colour=discord.Colour.green()
            )
            date = await self.bot.get_cog("TimeCog").date(member.created_at, year=True)
            embed.add_field(name="Compte créé le", value=date)
        else:
            embed = discord.Embed(
                title="Départ d'un membre",
                description=member.mention + " a quitté votre serveur",
                colour=discord.Colour(15994684)
            )
            delta = await self.bot.get_cog("TimeCog").time_delta(member.joined_at, datetime.datetime.utcnow(), lang="fr", year=True, precision=0)
            embed.add_field(name=f"Dans le serveur depuis", value=delta)
        embed.set_author(name=str(member), icon_url=member.avatar_url_as(static_format='png'))
        embed.set_footer(text=f"Member ID: {member.id}")
        await self.send_embed(member.guild, embed)
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_member_ban"
        if not await self.has_logs(guild):
            return
        if 'moderation' not in self.get_flags(guild.id):
            return
        embed = discord.Embed(
            title="Membre banni",
            description=f"Le membre {user.mention} vient d'être banni",
            colour=discord.Colour.red()
        )
        embed.set_author(name=str(user), icon_url=user.avatar_url_as(static_format='png'))
        embed.set_footer(text=f"Member ID: {user.id}")
        await self.send_embed(guild, embed)
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_member_unban"
        if not await self.has_logs(guild):
            return
        if 'moderation' not in self.get_flags(guild.id):
            return
        embed = discord.Embed(
            title="Membre débanni",
            description=f"Le membre {user.mention} n'est plus banni",
            colour=discord.Colour.green()
        )
        embed.set_author(name=str(user), icon_url=user.avatar_url_as(static_format='png'))
        embed.set_footer(text=f"User ID: {user.id}")
        await self.send_embed(guild, embed)
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_voice_state_update"
        if not await self.has_logs(member.guild):
            return
        if 'voice' not in self.get_flags(member.guild.id):
            return
        # member joined a channel
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                title="Mouvement en vocal",
                description=f"Le membre {member.mention} vient de rejoindre le salon {after.channel.name}"
            )
        # member left a channel
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                title="Mouvement en vocal",
                description=f"Le membre {member.mention} vient de quitter le salon {before.channel.name}"
            )
        # member moved in another channel
        elif before.channel != after.channel:
            embed = discord.Embed(
                title="Mouvement en vocal",
                description=f"Le membre {member.mention} est passé du salon {before.channel.name} au salon {after.channel.name}"
            )
        embed.colour = discord.Color.light_gray()
        embed.set_author(name=str(member), icon_url=member.avatar_url_as(static_format='png'))
        embed.set_footer(text=f"Member ID: {member.id}")
        await self.send_embed(member.guild, embed)
    
    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_guild_update"
        if before.premium_subscription_count == after.premium_subscription_count:
            return # not interesting
        if not await self.has_logs(after):
            return
        if 'boosts' not in self.get_flags(after.id):
            return
        if before.premium_subscription_count < after.premium_subscription_count:
            embed = discord.Embed(
                title="Nouveau boost",
                description=f"Votre serveur a reçu un nouveau boost !"
            )
        else:
            embed = discord.Embed(
                title="Boost perdu",
                description=f"Votre serveur vient de perdre un boost"
            )
        if before.premium_tier != after.premium_tier:
            embed.description += f"\nVous êtes passé du niveau {before.premium_tier} au niveau {after.premium_tier}"
        embed.color = discord.Color(0xf47fff)
        await self.send_embed(after, embed)


def setup(bot):
    bot.add_cog(Logs(bot))
