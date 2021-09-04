import asyncio
import io
import json
import re
from typing import Any, List, Union

import args
import checks
import discord
import emoji
from discord.ext import commands
from utils import CONFIG_OPTIONS, Gunibot, MyContext


class Sconfig(commands.Cog):

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "sconfig"
        self.sorted_options = dict() # config options sorted by cog
        self.config_options = ['prefix']
        for cog in bot.cogs.values():
            if not hasattr(cog, 'config_options'):
            # if the cog doesn't have any specific config
                continue
            self.sorted_options[cog.__cog_name__] = {k: v for k, v in CONFIG_OPTIONS.items() if k in cog.config_options}
        # for whatever reason, the for loop above doesn't include its own cog, so we just force it
        self.sorted_options[self.__cog_name__] = {k: v for k, v in CONFIG_OPTIONS.items() if k in self.config_options}
    
    def on_anycog_load(self, cog: commands.Cog):
        """Used to enable config commands when a cog is enabled
        
        Parameters
        -----------
        cog: :class:`commands.Cog`
            The cog which got enabled"""
        if not hasattr(cog, 'config_options'):
            # if the cog doesn't have any specific config
            return
        self.sorted_options[cog.__cog_name__] = {k: v for k, v in CONFIG_OPTIONS.items() if k in cog.config_options}
        for opt in self.sorted_options[cog.__cog_name__].values():
            # we enable the commands if needed
            if 'command' in opt:
                try:
                    self.bot.get_command("config "+opt['command']).enabled = True
                except AttributeError:
                    # if the command doesn't exist
                    pass
    
    def on_anycog_unload(self, cog: str):
        """Used to disable config commands when a cog is disabled
        
        Parameters
        -----------
        cog: :class:`str`
            The name of the disabeld cog"""
        if cog in self.sorted_options:
            for opt in self.sorted_options[cog].values():
                # we disable the commands if needed
                if 'command' in opt:
                    try:
                        self.bot.get_command("config "+opt['command']).enabled = False
                    except AttributeError:
                        # if the command doesn't exist
                        pass
            del self.sorted_options[cog]

    async def edit_config(self, guildID: int, key: str, value: Any):
        """Edit or reset a config option for a guild
        
        Parameters
        -----------
        guildID: :class:`int`
            The ID of the concerned guild

        key: :class:`str`
            The name of the option to edit
        
        value: :class:`Any`
            The new value of the config, or None to reset"""
        if value is None:
            del self.bot.server_configs[guildID][key]
            return await self.bot._(guildID, "sconfig.option-reset", opt=key)
        try:
            self.bot.server_configs[guildID][key] = value
        except ValueError:
            return await self.bot._(guildID, "sconfig.option-notfound", opt=key)
        else:
            return await self.bot._(guildID, "sconfig.option-edited", opt=key)

    async def format_config(self, guild: discord.Guild, key: str, value: str, mention: bool = True) -> str:
        if value is None:
            return None
        config = CONFIG_OPTIONS[key]

        def getname(x): return (x.mention if mention else x.name)

        sep = ' ' if mention else ' | '
        if key == "levelup_channel":
            if value in (None, 'none', 'any'):
                return str(value).capitalize()
        if config['type'] == 'roles':
            value = [value] if isinstance(value, int) else value
            roles = [guild.get_role(x) for x in value]
            roles = [getname(x) for x in roles if x is not None]
            return sep.join(roles)
        if config['type'] == 'channels':
            value = [value] if isinstance(value, int) else value
            channels = [guild.get_channel(x) for x in value]
            channels = [getname(x) for x in channels if x is not None]
            return sep.join(channels)
        if config['type'] == 'categories':
            value = [value] if isinstance(value, int) else value
            categories = [guild.get_channel(x) for x in value]
            categories = [x.name for x in categories if x is not None]
            return " | ".join(categories)
        if config['type'] == 'duration':
            return await self.bot.get_cog("TimeCog").time_delta(value, lang='fr', year=True, precision=0)
        if config['type'] == 'emojis':
            def emojis_convert(s_emoji:str, bot_emojis:List[discord.Emoji]) -> Union[str, discord.Emoji]:
                if s_emoji.isnumeric():
                    d_em = discord.utils.get(bot_emojis, id=int(s_emoji))
                    if d_em is None:
                        return ":deleted_emoji:"
                    else:
                        return f":{d_em.name}:"
                return emoji.emojize(s_emoji, use_aliases=True)
            value = [value] if isinstance(value, str) else value
            return " ".join([emojis_convert(x, self.bot.emojis) for x in value])
        if config['type'] == 'modlogsFlags':
            flags = self.bot.get_cog("ConfigCog").LogsFlags().intToFlags(value)
            return " - ".join(flags) if len(flags) > 0 else None
        if config['type'] == 'language':
            cog = self.bot.get_cog("Languages")
            if cog:
                return cog.languages[value]
            return value
        if config['type'] == 'int':
            return value
        return value

    @commands.group(name="config")
    @commands.guild_only()
    @commands.check(checks.is_admin)
    async def main_config(self, ctx: MyContext):
        """Edit your server configuration"""
        if ctx.subcommand_passed is None:
            res = list()
            # get the server config
            config = ctx.bot.server_configs[ctx.guild.id]
            # get the length of the longest key
            max_length = 0
            for options in self.sorted_options.values():
                max_length = max(max_length, *[len(k) for k in config.keys() if k in options])
            max_length += 2
            # iterate over groups
            for module, options in sorted(self.sorted_options.items()):
                subconf = {k:v for k,v in config.items() if k in options}
                if len(subconf) == 0:
                    continue
                temp = "   # {}\n".format(await self.bot._(ctx.guild.id, "sconfig.cog-name."+module))
                # iterate over configs for that group
                for k, v in subconf.items():
                    value = await self.format_config(ctx.guild, k, v, False)
                    temp += (f"[{k}]").ljust(max_length+1) + f" {value}\n"
                if hasattr(self.bot.get_cog(module), '_create_config'):
                    for extra in await self.bot.get_cog(module)._create_config(ctx):
                        temp += (f"[{extra[0]}]").ljust(max_length+1) + f" {extra[1]}\n"
                res.append(temp)

            for category in res:
                await ctx.send("```ini\n" + "\n" + category + "```")

        elif ctx.invoked_subcommand is None:
            await ctx.send(await self.bot._(ctx.guild.id, 'sconfig.option-notfound'))

    @main_config.command(name="prefix")
    async def config_prefix(self, ctx: MyContext, new_prefix=None):
        limit = 7
        if new_prefix is not None and len(new_prefix) > limit:
            await ctx.send(await self.bot._(ctx.guild.id, "sconfig.prefix-too-long", c=limit))
            return
        await ctx.send(await self.edit_config(ctx.guild.id, "prefix", new_prefix))

    @main_config.command(name="logs_channel")
    async def config_logs_channel(self, ctx: MyContext, *, channel: discord.TextChannel):
        await ctx.send(await self.edit_config(ctx.guild.id, "logs_channel", channel.id))
        if logs_cog := self.bot.get_cog("Logs"):
            emb = discord.Embed(title=await self.bot._(ctx.guild, "sconfig.config-enabled"),
                                description=await self.bot._(ctx.guild, "sconfig.modlogs-channel-enabled"),
                                color=16098851)
            await logs_cog.send_embed(ctx.guild, emb)

    #--------------------------------------------------
    # Contact
    #--------------------------------------------------

    @main_config.command(name="contact_channel")
    async def config_contact_channel(self, ctx: MyContext, *, channel: discord.TextChannel):
        await ctx.send(await self.edit_config(ctx.guild.id, "contact_channel", channel.id))

    @main_config.command(name="contact_category")
    async def config_contact_category(self, ctx: MyContext, *, category: discord.CategoryChannel):
        await ctx.send(await self.edit_config(ctx.guild.id, "contact_category", category.id))

    @main_config.command(name="contact_roles")
    async def config_contact_roles(self, ctx: MyContext, roles: commands.Greedy[discord.Role]):
        if len(roles) == 0:
            roles = None
        else:
            roles = [role.id for role in roles]
        await ctx.send(await self.edit_config(ctx.guild.id, "contact_roles", roles))

    @main_config.command(name="contact_title")
    async def config_contact_title(self, ctx: MyContext, *, title):
        if title == "author" or title == "object":
            await ctx.send(await self.edit_config(ctx.guild.id, "contact_title", title))
        else:
            await ctx.send(await self.bot._(ctx.guild.id, "contact.invalid-title"))

    #--------------------------------------------------
    # Welcome
    #--------------------------------------------------

    @main_config.command(name="welcome_roles")
    async def config_welcome_roles(self, ctx: MyContext, roles: commands.Greedy[discord.Role]):
        if len(roles) == 0:
            roles = None
        else:
            roles = [role.id for role in roles]
        await ctx.send(await self.edit_config(ctx.guild.id, "welcome_roles", roles))

    @main_config.command(name="info_channel")
    async def config_info_channel(self, ctx: MyContext, *, channel: discord.TextChannel):
        await ctx.send(await self.edit_config(ctx.guild.id, "info_channel", channel.id))

    @main_config.command(name="verification_role")
    async def config_verification_role(self, ctx: MyContext, *, role: discord.Role):
        await ctx.send(await self.edit_config(ctx.guild.id, "verification_role", role.id))

    @main_config.command(name="verification_add_role")
    async def config_verification_add_role(self, ctx: MyContext, value: bool):
        await ctx.send(await self.edit_config(ctx.guild.id, "verification_add_role", value))

    @main_config.command(name="verification_info_message")
    async def config_verification_add_role(self, ctx: MyContext, *, value: str = None):
        """Informative message sent in the verification channel when someone joins your message
        Put nothing to reset it, or "None" for no message"""
        if value.lower() == "none":
            value = "None"  # no message
        await ctx.send(await self.edit_config(ctx.guild.id, "verification_info_message", value))

    @main_config.command(name="pass_message")
    async def config_pass_message(self, ctx: MyContext, *, message):
        await ctx.send(await self.edit_config(ctx.guild.id, "pass_message", message))

    @main_config.command(name="verification_channel")
    async def config_verification_channel_id(self, ctx: MyContext, *, channel: discord.TextChannel):
        await ctx.send(await self.edit_config(ctx.guild.id, "verification_channel", channel.id))

    #--------------------------------------------------
    # Voice Channel
    #--------------------------------------------------

    @main_config.command(name="voice_channel_format")
    async def config_voice_channel_format(self, ctx: MyContext, *, text: str):
        """Format of voice channels names
        Use {random} for any random name, {asterix} for any asterix name"""
        await ctx.send(await self.edit_config(ctx.guild.id, "voice_channel_format", text[:40]))

    @main_config.command(name="voice_roles")
    async def config_voice_roles(self, ctx: MyContext, roles: commands.Greedy[discord.Role]):
        if len(roles) == 0:
            roles = None
        else:
            roles = [role.id for role in roles]
        await ctx.send(await self.edit_config(ctx.guild.id, "voice_roles", roles))

    @main_config.command(name="voices_category")
    async def config_voices_category(self, ctx: MyContext, *, category: discord.CategoryChannel):
        await ctx.send(await self.edit_config(ctx.guild.id, "voices_category", category.id))

    @main_config.command(name="voice_channel")
    async def config_voice_channel(self, ctx: MyContext, *, channel: discord.VoiceChannel):
        await ctx.send(await self.edit_config(ctx.guild.id, "voice_channel", channel.id))

    #--------------------------------------------------
    # ModLogs
    #--------------------------------------------------

    @main_config.command(name="modlogs_flags")
    async def config_modlogs_flags(self, ctx: MyContext):
        await ctx.send(await self.bot._(ctx.guild.id, "sconfig.modlogs-help", p=ctx.prefix))

    @main_config.group(name="modlogs")
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
        flags = list(set(flags)) # remove duplicates
        await self.edit_config(ctx.guild.id, 'modlogs_flags',
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
        await self.edit_config(ctx.guild.id, 'modlogs_flags', LogsFlags.flagsToInt(flags))
        await ctx.send(await self.bot._(ctx.guild.id, "sconfig.modlogs-disabled", type=', '.join(options)))

    @config_modlogs.command(name="list")
    async def modlogs_list(self, ctx: MyContext):
        """See available logs categories"""
        f = self.bot.get_cog('ConfigCog').LogsFlags.FLAGS.values()
        await ctx.send(await self.bot._(ctx.guild.id, "sconfig.modlogs-list", list=" - ".join(f)))

    #--------------------------------------------------
    # Thanks
    #--------------------------------------------------

    @main_config.command(name="thanks_allowed_roles")
    async def config_thanks_allowed_roles(self, ctx: MyContext, roles: commands.Greedy[discord.Role]):
        if len(roles) == 0:
            roles = None
        else:
            roles = [role.id for role in roles]
        await ctx.send(await self.edit_config(ctx.guild.id, "thanks_allowed_roles", roles))

    @main_config.command(name="thanks_duration")
    async def config_thanks_duration(self, ctx: MyContext, duration: commands.Greedy[args.tempdelta]):
        duration = sum(duration)
        if duration == 0:
            if ctx.message.content.split(" ")[-1] != "thanks_duration":
                await ctx.send(await self.bot._(ctx.guild.id, "sconfig.invalid-duration"))
                return
            duration = None
        x = await self.edit_config(ctx.guild.id, "thanks_duration", duration)
        await ctx.send(x)

    @main_config.group(name="thanks", aliases=['thx'], enabled=False)
    async def thanks_main(self, ctx: MyContext):
        """Edit your thanks-levels settings"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("config thanks")

    @thanks_main.command(name="list")
    async def thanks_list(self, ctx: MyContext):
        """List your current thanks levels"""
        await self.bot.get_cog("Thanks").thankslevels_list(ctx)

    @thanks_main.command(name="add")
    async def thanks_add(self, ctx: MyContext, amount: int, role: discord.Role):
        """Add a role to give when someone reaches a certain amount of thanks"""
        await self.bot.get_cog("Thanks").thankslevel_add(ctx, amount, role)
    
    @thanks_main.command(name="reset")
    async def thanks_reset(self, ctx: MyContext, amount: int = None):
        """Remove every role given for a certain amount of thanks
        If no amount is specified, it will reset the whole configuration"""
        if amount is None:
            await self.bot.get_cog("Thanks").thankslevel_reset(ctx)
        else:
            await self.bot.get_cog("Thanks").thankslevel_remove(ctx, amount)

    #--------------------------------------------------
    # Language
    #--------------------------------------------------

    @main_config.command(name="language", aliases=['lang'])
    async def language(self, ctx: MyContext, lang: str):
        """Change the bot language in your server
        Use the 'list' option to get the available languages"""
        cog = self.bot.get_cog("Languages")
        if not cog:  # if cog not loaded
            await ctx.send("Unable to load languages, please try again later")
        elif lang == "list":  # send a list of available languages
            availabe = " - ".join(cog.languages)
            await ctx.send(await self.bot._(ctx.guild.id, "sconfig.languages-list", list=availabe))
        elif lang not in cog.languages:  # invalid language
            await ctx.send(await self.bot._(ctx.guild.id, 'sconfig.invalid-language', p=ctx.prefix))
        else:  # correct case
            selected = cog.languages.index(lang)
            await ctx.send(await self.edit_config(ctx.guild.id, "language", selected))

    #--------------------------------------------------
    # Hypesquad
    #--------------------------------------------------

    @main_config.group(name="hypesquad", aliases=['hs'], enabled=False)
    async def hs_main(self, ctx: MyContext):
        """Manage options about Discord ypesquads"""
        if ctx.subcommand_passed is None:
            await ctx.send_help("config hypesquad")
    
    @hs_main.command(name="role")
    async def hs_role(self, ctx: MyContext, house: str, *, role: discord.Role=None):
        """Set a role to give to a hypesquad house members
        Valid houses are: bravery, brilliance, balance and none"""
        role = role.id if isinstance(role, discord.Role) else None
        house = house.lower()
        if house == 'none':
            await ctx.send(await self.edit_config(ctx.guild.id, "hs_none_role", role))
        elif house == 'bravery':
            await ctx.send(await self.edit_config(ctx.guild.id, "hs_bravery_role", role))
        elif house == 'brilliance':
            await ctx.send(await self.edit_config(ctx.guild.id, "hs_brilliance_role", role))
        elif house == 'balance':
            await ctx.send(await self.edit_config(ctx.guild.id, "hs_balance_role", role))
        else:
            await ctx.send(await self.bot._(ctx.guild.id, 'sconfig.hypesquad.unknown'))

    #--------------------------------------------------
    # Giveaway
    #--------------------------------------------------

    @main_config.command(name="giveaways_emojis")
    async def giveaways_emojis(self, ctx: MyContext, emojis: commands.Greedy[Union[discord.Emoji, str]]):
        """Set a list of usable emojis for giveaways
        Only these emojis will be usable to participate in a giveaway
        If no emoji is specified, every emoji will be usable"""
        # check if every emoji is valid
        unicode_re = emoji.get_emoji_regexp()
        emojis = [x for x in emojis if isinstance(x, discord.Emoji) or re.fullmatch(unicode_re, x)]
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
        await ctx.send(await self.edit_config(ctx.guild.id, "giveaways_emojis", emojis))

    #--------------------------------------------------
    # XP
    #--------------------------------------------------

    @main_config.command(name="enable_xp")
    async def config_enable_xp(self, ctx: MyContext, value: bool):
        """Enable or disable the XP system in your server"""
        await ctx.send(await self.edit_config(ctx.guild.id, "enable_xp", value))
    
    @main_config.command(name="noxp_channels")
    async def config_noxp_channels(self, ctx: MyContext, channels: commands.Greedy[discord.TextChannel]):
        """Select in which channels your members should not get any xp"""
        if len(channels) == 0:
            channels = None
        x = await self.edit_config(ctx.guild.id, "noxp_channels", channels)
        await ctx.send(x)
    
    @main_config.command(name="levelup_channel")
    async def config_levelup_channel(self, ctx: MyContext, *, channel):
        """Select in which channel the levelup messages should be sent
        None for no levelup message, any for any channel"""
        if channel.lower() == 'none':
            channel = 'none'
        elif channel.lower() == 'any':
            channel = 'any'
        else:
            channel = await commands.TextChannelConverter().convert(ctx, channel)
            channel = channel.id
        await ctx.send(await self.edit_config(ctx.guild.id, "levelup_channel", channel))
    
    @main_config.command(name="levelup_message")
    async def config_levelup_message(self, ctx: MyContext, *, message=None):
        """Message sent when a member reaches a new level
        Use {level} for the new level, {user} for the user mention and {username} for the user name
        Set to None to reset it"""
        await ctx.send(await self.edit_config(ctx.guild.id, "levelup_message", message))

    @main_config.command(name="levelup_reaction")
    async def config_levelup_reaction(self, ctx: MyContext, *, bool: bool=None):
        """If the bot add a reaction to the message or send a message
        Set to True for the reaction, False for the message"""
        await ctx.send(await self.edit_config(ctx.guild.id, "levelup_reaction", bool))

    @main_config.command(name="reaction_emoji")
    async def config_levelup_reaction_emoji(self, ctx: MyContext, emote: discord.Emoji=None):
        """Set the emoji wich one the bot will react to message when levelup"""
        # check if emoji is valid
        unicode_re = emoji.get_emoji_regexp()
        emote = emote if isinstance(emote, discord.Emoji) or re.fullmatch(unicode_re, emote) else False
        # if emojis was invalid (couldn't be converted)
        if not emote:
            await ctx.send(await self.bot._(ctx.guild.id, "sconfig.invalid-emoji"))
            return
        # convert discord emoji to ID if needed
        emote = str(emote.id) if isinstance(emote, discord.Emoji) else emote
        # save result
        await ctx.send(await self.edit_config(ctx.guild.id, "reaction_emoji", emote))

    #--------------------------------------------------
    # Groups
    #--------------------------------------------------

    @main_config.command(name="group_allowed_role")
    async def config_group_allowed_role(self, ctx: MyContext, *, role: discord.Role=None):
        """Role allowed to create groups"""
        role = role.id if isinstance(role, discord.Role) else None
        await ctx.send(await self.edit_config(ctx.guild.id, "group_allowed_role", role))

    @main_config.command(name="group_channel_category")
    async def config_group_channel_category(self, ctx: MyContext, *, category: discord.CategoryChannel):
        """Category were group channel will be created"""
        await ctx.send(await self.edit_config(ctx.guild.id, "group_channel_category", category.id))

    @main_config.command(name="group_over_role")
    async def config_group_over_role(self, ctx: MyContext, *, role: discord.Role = None):
        """Role under the groups roles will be created"""
        role = role.id if isinstance(role, discord.Role) else None
        await ctx.send(await self.edit_config(ctx.guild.id, "group_over_role", role))

    @main_config.command(name="max_group")
    async def config_max_group(self, ctx: MyContext, *, number: int = None):
        """Max groups by user"""
        await ctx.send(await self.edit_config(ctx.guild.id, "max_group", number))

    @commands.group(name="config-backup", aliases=["config-bkp"])
    @commands.guild_only()
    @commands.check(checks.is_admin)
    async def config_backup(self, ctx: MyContext):
        """Create or load your server configuration"""
        if ctx.subcommand_passed is None:
            await ctx.send_help('config-backup')

    #--------------------------------------------------
    # Backup
    #--------------------------------------------------

    @config_backup.command(name="get", aliases=["create"])
    async def backup_create(self, ctx: MyContext):
        "Create a backup of your configuration"
        data = json.dumps(self.bot.server_configs[ctx.guild.id])
        data = io.BytesIO(data.encode("utf8"))
        txt = await self.bot._(ctx.guild.id, "sconfig.backup.ended")
        await ctx.send(txt, file=discord.File(data, filename="config-backup.json"))

    @config_backup.command(name="load")
    async def backup_load(self, ctx: MyContext):
        "Load a backup of your configuration (in attached file) and apply it"
        if not (ctx.message.attachments and ctx.message.attachments[0].filename.endswith(".json")):
            await ctx.send(await self.bot._(ctx.guild.id, "sconfig.backup.nofile"))
            return
        data = json.loads(await ctx.message.attachments[0].read())
        conf = self.bot.server_configs[ctx.guild.id]
        for k in data.keys():
            if not k in conf.keys():
                await ctx.send(await self.bot._(ctx.guild.id, "sconfig.backup.invalidfile"))
                return
        merge = {k: v for k, v in data.items() if v != conf[k]}
        if len(merge) == 0:
            await ctx.send(await self.bot._(ctx.guild.id, "sconfig.backup.noedit"))
            return
        msg = await ctx.send(await self.bot._(ctx.guild.id, "sconfig.backup.check", count=len(merge)))
        await msg.add_reaction("✅")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == "✅" and reaction.message.id == msg.id
        try:
            await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(await self.bot._(ctx.guild.id, "sconfig.backup.timeout"))
        else:
            d = dict(self.bot.server_configs[ctx.guild.id])
            d.update(merge)
            self.bot.server_configs[ctx.guild.id] = d
            await ctx.send('👍')

    #--------------------------------------------------
    # Archives
    #--------------------------------------------------

    @main_config.command(name="archive_category")
    async def config_voice_channel(self, ctx: MyContext, *, category: discord.CategoryChannel):
        await ctx.send(await self.edit_config(ctx.guild.id, "archive_category", category.id))

    @main_config.command(name="archive_duration")
    async def config_archive_duration(self, ctx: MyContext, duration: commands.Greedy[args.tempdelta]):
        duration = sum(duration)
        if duration == 0:
            if ctx.message.content.split(" ")[-1] != "archive_duration":
                await ctx.send(await self.bot._(ctx.guild.id, "sconfig.invalid-duration"))
                return
            duration = None
        x = await self.edit_config(ctx.guild.id, "archive_duration", duration)
        await ctx.send(x)


def setup(bot):
    bot.add_cog(Sconfig(bot))
