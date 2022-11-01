import datetime
from typing import List

import discord
from discord.ext import commands
from utils import Gunibot, MyContext
from bot.utils.sconfig import SERVER_CONFIG
import args


class Logs(commands.Cog):

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.config_options = ['logs_channel', 'modlogs_flags']

        bot.get_command("config").add_command(self.config_modlogs_flags)
        bot.get_command("config").add_command(self.config_modlogs)

    @commands.command(name="modlogs_flags")
    async def config_modlogs_flags(self, ctx: MyContext):
        await ctx.send(await self.bot._(ctx.guild.id, "sconfig.modlogs-help", p=ctx.prefix))

    @commands.group(name="modlogs")
    async def config_modlogs(self, ctx: MyContext):
        """Enable or disable logs categories in your logs channel
        You can set your channel with the 'logs_channel' config option"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("config modlogs")

    @config_modlogs.command(name="enable")
    async def modlogs_enable(self, ctx: MyContext, options: commands.Greedy[args.moderatorFlag]):
        """Enable one or multiple logs categories"""
        if not options:
            await ctx.send(await self.bot._(ctx.guild.id, "sconfig.invalid-modlogs"))
            return
        LogsFlags = self.bot.get_cog('ConfigCog').LogsFlags()
        flags = self.bot.server_configs[ctx.guild.id]['modlogs_flags']
        flags = LogsFlags.intToFlags(flags) + options
        flags = list(set(flags))  # remove duplicates
        await SERVER_CONFIG.edit_config(ctx.guild.id, 'modlogs_flags',
                                  LogsFlags.flagsToInt(flags))
        await ctx.send(await self.bot._(ctx.guild.id, "sconfig.modlogs-enabled", type=', '.join(options)))

    @config_modlogs.command(name="disable")
    async def modlogs_disable(self, ctx: MyContext, options: commands.Greedy[args.moderatorFlag]):
        """Disable one or multiple logs categories"""
        if not options:
            await ctx.send(await self.bot._(ctx.guild.id, "sconfig.invalid-modlogs"))
            return
        LogsFlags = self.bot.get_cog('ConfigCog').LogsFlags()
        flags = self.bot.server_configs[ctx.guild.id]['modlogs_flags']
        flags = LogsFlags.intToFlags(flags)
        flags = [x for x in flags if x not in options]
        await SERVER_CONFIG.edit_config(ctx.guild.id, 'modlogs_flags', LogsFlags.flagsToInt(flags))
        await ctx.send(await self.bot._(ctx.guild.id, "sconfig.modlogs-disabled", type=', '.join(options)))

    @config_modlogs.command(name="list")
    async def modlogs_list(self, ctx: MyContext):
        """See available logs categories"""
        f = self.bot.get_cog('ConfigCog').LogsFlags.FLAGS.values()
        await ctx.send(await self.bot._(ctx.guild.id, "sconfig.modlogs-list", list=" - ".join(f)))

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
            title=await self.bot._(message.guild.id, "logs.msg_delete.title"),
            description=await self.bot._(message.guild.id, "logs.msg_delete.desc", author=message.author.mention, channel=message.channel.mention),
            colour=discord.Colour(13632027)
        )
        embed.set_author(name=str(message.author),
                         icon_url=message.author.avatar_url)
        _footer = await self.bot._(message.guild.id, "logs.footer1", author=message.author.id, message=message.id)
        embed.set_footer(text=_footer)
        if len(message.content) > 1024:
            message.content = message.content[:1020] + '...'
        _content = await self.bot._(message.guild.id, "logs.msg_delete.content")
        embed.add_field(name=_content, value=message.content)
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
            title=await self.bot._(before.guild.id, "logs.msg_edit.title"),
            description=await self.bot._(before.guild.id, "logs.msg_edit.desc", url=before.jump_url, author=before.author.mention, channel=before.channel.mention),
            colour=discord.Colour(16294684)
        )
        embed.set_author(name=str(before.author),
                         icon_url=before.author.avatar_url)
        _footer = await self.bot._(before.guild.id, "logs.footer1", author=before.author.id, message=before.id)
        embed.set_footer(text=_footer)
        if len(before.content) > 1024:
            before.content = before.content[:1020] + '...'
        if len(after.content) > 1024:
            after.content = after.content[:1020] + '...'
        _before = await self.bot._(before.guild.id, "logs.before")
        _after = await self.bot._(before.guild.id, "logs.after")
        embed.add_field(name=_before, value=before.content, inline=False)
        embed.add_field(name=_after, value=after.content, inline=False)
        await self.send_embed(before.guild, embed)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_raw_bulk_message_delete"
        guild = self.bot.get_guild(payload.guild_id)
        if not await self.has_logs(guild):
            return
        if 'messages' not in self.get_flags(guild.id):
            return
        count = len(payload.message_ids)
        embed = discord.Embed(
            timestamp=datetime.datetime.utcnow(),
            title=await self.bot._(payload.guild_id, "logs.bulk_delete.title"),
            description=await self.bot._(payload.guild_id, "logs.bulk_delete.desc", count=count, channel=payload.channel_id),
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
            title=await self.bot._(invite.guild.id, "logs.invite_created.title"),
            description=await self.bot._(invite.guild.id, "logs.invite_created.desc", channel=invite.channel.mention),
            colour=discord.Colour.green()
        )
        if invite.inviter:  # sometimes Discord doesn't send that info
            embed.set_author(
                name=f'{invite.inviter.name}#{invite.inviter.discriminator}',
                icon_url=invite.inviter.avatar_url_as(
                    static_format='png'))
            _footer = await self.bot._(invite.guild.id, "logs.footer2", author=invite.inviter.id)
            embed.set_footer(text=_footer)
        _duration = await self.bot._(invite.guild.id, "logs.invite_created.duration")
        if invite.max_age == 0:
            embed.add_field(name=_duration, value="♾")
        else:
            embed.add_field(
                name=_duration,
                value=f"{datetime.timedelta(seconds=invite.max_age)}")
        embed.add_field(name="URL", value=invite.url)
        _max_uses = await self.bot._(invite.guild.id, "logs.invite_created.max_uses")
        embed.add_field(
            name=_max_uses,
            value="♾" if invite.max_uses == 0 else str(
                invite.max_uses))
        await self.send_embed(invite.guild, embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_invite_delete"
        if not await self.has_logs(invite.guild):
            return
        if 'invites' not in self.get_flags(invite.guild.id):
            return
        embed = discord.Embed(
            title=await self.bot._(invite.guild.id, "logs.invite_delete.title"),
            description=await self.bot._(invite.guild.id, "logs.invite_delete.desc", channel=invite.channel.mention),
            colour=discord.Colour.green()
        )
        if invite.inviter:
            embed.set_author(
                name=f'{invite.inviter.name}#{invite.inviter.discriminator}',
                icon_url=invite.inviter.avatar_url_as(
                    static_format='png'))
            _footer = await self.bot._(invite.guild.id, "logs.footer2", author=invite.inviter.id)
            embed.set_footer(text=_footer)
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
                title=await self.bot._(member.guild.id, "logs.member_join.title"),
                description=await self.bot._(member.guild.id, "logs.member_join.desc", user=member.mention),
                colour=discord.Colour.green()
            )
            date = await self.bot.get_cog("TimeCog").date(member.created_at, year=True)
            _date = await self.bot._(member.guild.id, "logs.member_join.date")
            embed.add_field(name=_date, value=date)
        else:
            embed = discord.Embed(
                title=await self.bot._(member.guild.id, "logs.member_left.title"),
                description=await self.bot._(member.guild.id, "logs.member_left.desc", user=member.mention),
                colour=discord.Colour(15994684)
            )
            delta = await self.bot.get_cog("TimeCog").time_delta(member.joined_at, datetime.datetime.utcnow(), lang="fr", year=True, precision=0)
            _date = await self.bot._(member.guild.id, "logs.member_left.date")
            embed.add_field(name=_date, value=delta)
        embed.set_author(name=str(member), icon_url=member.avatar_url)
        _footer = await self.bot._(member.guild.id, "logs.footer3", member=member.id)
        embed.set_footer(text=_footer)
        await self.send_embed(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_member_ban"
        if not await self.has_logs(guild):
            return
        if 'moderation' not in self.get_flags(guild.id):
            return
        embed = discord.Embed(
            title=await self.bot._(guild.id, "logs.member_ban.title"),
            description=await self.bot._(guild.id, "logs.member_ban.desc", user=user.mention),
            colour=discord.Colour.red()
        )
        embed.set_author(name=str(user), icon_url=user.avatar_url)
        _footer = await self.bot._(guild.id, "logs.footer3", member=user.id)
        embed.set_footer(text=_footer)
        await self.send_embed(guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_member_unban"
        if not await self.has_logs(guild):
            return
        if 'moderation' not in self.get_flags(guild.id):
            return
        embed = discord.Embed(
            title=await self.bot._(guild.id, "logs.member_unban.title"),
            description=await self.bot._(guild.id, "logs.member_unban.desc", user=user.mention),
            colour=discord.Colour.green()
        )
        embed.set_author(
            name=str(user), icon_url=user.avatar_url_as(static_format='png'))
        _footer = await self.bot._(guild.id, "logs.footer3", member=user.id)
        embed.set_footer(text=_footer)
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
            _desc = "join"
            kw = {'after': after.channel.name}
        # member left a channel
        elif before.channel is not None and after.channel is None:
            _desc = "left"
            kw = {'before': before.channel.name}
        # member moved in another channel
        elif before.channel != after.channel:
            _desc = "move"
            kw = {'before': before.channel.name, 'after': after.channel.name}
        else:
            return
        _title = await self.bot._(member.guild.id, "logs.voice_move.title")
        embed = discord.Embed(
            title=_title,
            description=await self.bot._(member.guild.id, "logs.voice_move." + _desc, user=member.mention, **kw)
        )
        embed.colour = discord.Color.light_gray()
        embed.set_author(name=str(member), icon_url=member.avatar_url)
        _footer = await self.bot._(member.guild.id, "logs.footer3", member=member.id)
        embed.set_footer(text=_footer)
        await self.send_embed(member.guild, embed)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_guild_update"
        if before.premium_subscription_count == after.premium_subscription_count:
            return  # not interesting
        if not await self.has_logs(after):
            return
        if 'boosts' not in self.get_flags(after.id):
            return
        if before.premium_subscription_count < after.premium_subscription_count:
            embed = discord.Embed(
                title=await self.bot._(before.guild.id, "logs.boost.title-new"),
                description=await self.bot._(before.guild.id, "logs.boost.desc-new")
            )
        else:
            embed = discord.Embed(
                title=await self.bot._(before.guild.id, "logs.boost.title-lost"),
                description=await self.bot._(before.guild.id, "logs.boost.desc-lost")
            )
        if before.premium_tier != after.premium_tier:
            _desc = await self.bot._(before.guild.id, "logs.boost.change", before=before.premium_tier, after=after.premium_tier)
            embed.description += "\n" + _desc
        embed.color = discord.Color(0xf47fff)
        await self.send_embed(after, embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_guild_role_create"
        if not await self.has_logs(role.guild):
            return
        if 'roles' not in self.get_flags(role.guild.id):
            return
        embed = discord.Embed(
            title=await self.bot._(role.guild.id, "logs.role_created.title"),
            description=await self.bot._(role.guild.id, "logs.role_created.desc", mention=role.mention, name=role.name)
        )
        _no = await self.bot._(role.guild.id, "logs._no")
        _yes = await self.bot._(role.guild.id, "logs._yes")
        _pos = await self.bot._(role.guild.id, "logs.role_created.pos")
        _ment = await self.bot._(role.guild.id, "logs.role_created.mentionnable")
        data = [_pos + ' {role.position}',
                _ment + ' ' + (_yes if role.mentionable else _no)]
        if role.color != discord.Color.default():
            data.append(await self.bot._(role.guild.id, "logs.role_created.color") + f' {role.color}')
        if role.hoist:
            data.append(await self.bot._(role.guild.id, "logs.role_created.hoisted"))
        if role.permissions.administrator:
            data.append(await self.bot._(role.guild.id, "logs.role_created.admin"))
        _info = await self.bot._(role.guild.id, "logs.role_created.info")
        embed.add_field(name=_info, value="\n".join(data))
        embed.color = discord.Color.green()
        await self.send_embed(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_guild_role_delete"
        if not await self.has_logs(role.guild):
            return
        if 'roles' not in self.get_flags(role.guild.id):
            return
        embed = discord.Embed(
            title=await self.bot._(role.guild.id, "logs.role_deleted.title"),
            description=await self.bot._(role.guild.id, "logs.role_deleted.desc", name=role.name)
        )
        _no = await self.bot._(role.guild.id, "logs._no")
        _yes = await self.bot._(role.guild.id, "logs._yes")
        _pos = await self.bot._(role.guild.id, "logs.role_created.pos")
        _ment = await self.bot._(role.guild.id, "logs.role_created.mentionnable")
        data = [_pos + ' {role.position}',
                _ment + ' ' + (_yes if role.mentionable else _no)]
        if role.color != discord.Color.default():
            data.append(await self.bot._(role.guild.id, "logs.role_created.color") + f' {role.color}')
        if role.hoist:
            data.append(await self.bot._(role.guild.id, "logs.role_created.hoisted"))
        if role.permissions.administrator:
            data.append(await self.bot._(role.guild.id, "logs.role_created.admin"))
        if role.members:
            _mmbr = await self.bot._(role.guild.id, "logs.role_created.members")
            data.append(_mmbr + f' {len(role.members)}')
        _info = await self.bot._(role.guild.id, "logs.role_created.info")
        embed.add_field(name=_info, value="\n".join(data))
        embed.color = discord.Color.red()
        await self.send_embed(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        "https://discordpy.readthedocs.io/en/latest/api.html#discord.on_guild_role_update"
        if not await self.has_logs(before.guild):
            return
        if 'roles' not in self.get_flags(before.guild.id):
            return
        embed = discord.Embed(
            title=await self.bot._(after.guild.id, "logs.role_updated.title"),
            description=await self.bot._(after.guild.id, "logs.role_updated.desc", mention=after.mention, name=after.name)
        )
        _no = await self.bot._(after.guild.id, "logs._no")
        _yes = await self.bot._(after.guild.id, "logs._yes")
        data = list()
        if before.color != after.color:
            _color = await self.bot._(after.guild.id, "logs.role_created.color")
            data.append(_color + f" {before.color} -> {after.color}")
        if before.name != after.name:
            _name = await self.bot._(after.guild.id, "logs.role_updated.name")
            data.append(_name + f" {before.name} -> {after.name}")
        if before.permissions.administrator != after.permissions.administrator:
            b1 = _yes if before.permissions.administrator else _no
            b2 = _yes if after.permissions.administrator else _no
            _admin = await self.bot._(after.guild.id, "logs.role_created.admin")
            data.append(_admin + f": {b1} -> {b2}")
        if before.mentionable != after.mentionable:
            b1 = _yes if before.mentionable else _no
            b2 = _yes if after.mentionable else _no
            _ment = await self.bot._(after.guild.id, "logs.role_created.mentionnable")
            data.append(_ment + f": {b1} -> {b2}")
        if before.hoist != after.hoist:
            b1 = _yes if before.hoist else _no
            b2 = _yes if after.hoist else _no
            _hoist = await self.bot._(after.guild.id, "logs.role_created.hoisted")
            data.append(_hoist + f": {b1} -> {b2}")
        if len(data) == 0:
            return
        _changes = await self.bot._(after.guild.id, "logs.role_updated.changes")
        embed.add_field(name=_changes, value="\n".join(data))
        embed.color = discord.Color.orange()
        await self.send_embed(before.guild, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """https://discordpy.readthedocs.io/en/latest/api.html#discord.on_member_update"""
        if not await self.has_logs(before.guild):
            return
        if 'members' not in self.get_flags(before.guild.id):
            return
        embed = discord.Embed(title=await self.bot._(after.guild.id, "logs.member_update.title"),
                              color=discord.Color(0xf8bd1c))
        if before.nick != after.nick:
            _nick = await self.bot._(after.guild.id, "logs.member_update.nick")
            embed.add_field(name=_nick, value=f"{before.nick} -> {after.nick}")
        if before.roles != after.roles:
            got = [r.mention for r in after.roles if r not in before.roles]
            lost = [r.mention for r in before.roles if r not in after.roles]
            if got:
                _added = await self.bot._(after.guild.id, "logs.member_update.roles_added", count=len(got))
                embed.add_field(name=_added, value=" ".join(got), inline=False)
            if lost:
                _removed = await self.bot._(after.guild.id, "logs.member_update.roles_removed", count=len(lost))
                embed.add_field(
                    name=_removed, value=" ".join(lost), inline=False)
        if len(embed.fields) == 0:
            return
        embed.set_author(name=str(before),
                         icon_url=before.avatar_url_as(static_format='png'))
        _footer = await self.bot._(after.guild.id, "logs.footer3", member=before.id)
        embed.set_footer(text=_footer)
        await self.send_embed(before.guild, embed)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before: List[discord.Emoji], after: List[discord.Emoji]):
        """https://discordpy.readthedocs.io/en/latest/api.html#discord.on_guild_emojis_update"""
        if not await self.has_logs(guild):
            return
        if 'emojis' not in self.get_flags(guild.id):
            return
        embed = discord.Embed(title=await self.bot._(guild.id, "logs.emoji_update.title"),
                              color=discord.Color(0xf8d71c))
        new = [str(e) for e in after if e not in before]
        lost = [str(e) for e in before if e not in after]
        renamed = list()
        restrict = list()
        for b in before:
            for a in after:
                if a.id == b.id:
                    if a.name != b.name:
                        renamed.append(f'{a} :{b.name}: -> :{a.name}:')
                    if a.roles != b.roles:
                        a_roles = ' '.join([x.mention for x in a.roles])
                        b_roles = ' '.join([x.mention for x in b.roles])
                        restrict.append(f'{a} {b_roles} -> {a_roles}')
        if not (new or lost or renamed):
            # can happen when Discord fetch emojis from Twitch without any
            # change
            return
        if new:
            n = await self.bot._(guild.id, "logs.emoji_update.added", count=len(new))
            embed.add_field(name=n, value="".join(new), inline=False)
        if lost:
            n = await self.bot._(guild.id, "logs.emoji_update.removed", count=len(lost))
            embed.add_field(name=n, value="".join(lost), inline=False)
        if renamed:
            n = await self.bot._(guild.id, "logs.emoji_update.renamed", count=len(renamed))
            embed.add_field(name=n, value="\n".join(renamed), inline=False)
        if restrict:
            n = await self.bot._(guild.id, "logs.emoji_update.restrict", count=len(restrict))
            embed.add_field(name=n, value="\n".join(restrict), inline=False)
        await self.send_embed(guild, embed)

config = {}
async def setup(bot:Gunibot=None, plugin_config:dict=None):
    if bot is not None:
        await bot.add_cog(Logs(bot), icon="📜")
    if plugin_config is not None:
        global config
        config.update(plugin_config)
