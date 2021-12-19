import asyncio
import io
import json
import re
from typing import Any, List, Union

import sys
sys.path.append("./bot")
import args
import sys
sys.path.append("./bot")
import checks
import nextcord
import emoji
from nextcord.ext import commands
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

    async def format_config(self, guild: nextcord.Guild, key: str, value: str, mention: bool = True) -> str:
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
            def emojis_convert(s_emoji:str, bot_emojis:List[nextcord.Emoji]) -> Union[str, nextcord.Emoji]:
                if s_emoji.isnumeric():
                    d_em = nextcord.utils.get(bot_emojis, id=int(s_emoji))
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
                configs_len = [len(k) for k in config.keys() if k in options]
                max_length = max(max_length, *configs_len) if len(configs_len) > 0 else max_length
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
    async def config_logs_channel(self, ctx: MyContext, *, channel: nextcord.TextChannel):
        await ctx.send(await self.edit_config(ctx.guild.id, "logs_channel", channel.id))
        if logs_cog := self.bot.get_cog("Logs"):
            emb = nextcord.Embed(title=await self.bot._(ctx.guild, "sconfig.config-enabled"),
                                description=await self.bot._(ctx.guild, "sconfig.modlogs-channel-enabled"),
                                color=16098851)
            await logs_cog.send_embed(ctx.guild, emb)


    

    #--------------------------------------------------
    # Voice Channel
    #--------------------------------------------------

    

    #--------------------------------------------------
    # ModLogs
    #--------------------------------------------------

    #--------------------------------------------------
    # Thanks
    #--------------------------------------------------


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



    #--------------------------------------------------
    # Giveaway
    #--------------------------------------------------

    

    #--------------------------------------------------
    # XP
    #--------------------------------------------------

    

    #--------------------------------------------------
    # Groups
    #--------------------------------------------------

    

    #--------------------------------------------------
    # Backup
    #--------------------------------------------------
    """
    @config_backup.command(name="get", aliases=["create"])
    async def backup_create(self, ctx: MyContext):
        "Create a backup of your configuration"
        data = json.dumps(self.bot.server_configs[ctx.guild.id])
        data = io.BytesIO(data.encode("utf8"))
        txt = await self.bot._(ctx.guild.id, "sconfig.backup.ended")
        await ctx.send(txt, file=nextcord.File(data, filename="config-backup.json"))

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
    """

    #--------------------------------------------------
    # Archives
    #--------------------------------------------------


def setup(bot):
    bot.add_cog(Sconfig(bot))
