from typing import Any, List, Union

import discord
from discord.ext import commands
import emoji

from core import CONFIG_OPTIONS, Gunibot, MyContext, checks

SERVER_CONFIG = None

class Sconfig(commands.Cog):
    def __init__(self, bot: Gunibot):
        global SERVER_CONFIG
        SERVER_CONFIG = self
        self.bot = bot
        self.file = "sconfig"
        self.sorted_options = dict()  # config options sorted by cog
        self.config_options = ["prefix"]
        for cog in bot.cogs.values():
            if not hasattr(cog, "config_options"):
                # if the cog doesn't have any specific config
                continue
            self.sorted_options[cog.__cog_name__] = {
                k: v for k, v in CONFIG_OPTIONS.items() if k in cog.config_options
            }
        # for whatever reason, the for loop above doesn't include its own cog,
        # so we just force it
        self.sorted_options[self.__cog_name__] = {
            k: v for k, v in CONFIG_OPTIONS.items() if k in self.config_options
        }

    def on_anycog_load(self, cog: commands.Cog):
        """Used to enable config commands when a cog is enabled

        Parameters
        -----------
        cog: :class:`commands.Cog`
            The cog which got enabled"""
        if not hasattr(cog, "config_options"):
            # if the cog doesn't have any specific config
            return
        self.sorted_options[cog.__cog_name__] = {
            k: v for k, v in CONFIG_OPTIONS.items() if k in cog.config_options
        }
        for opt in self.sorted_options[cog.__cog_name__].values():
            # we enable the commands if needed
            if "command" in opt:
                try:
                    self.bot.get_command("config " + opt["command"]).enabled = True
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
                if "command" in opt:
                    try:
                        self.bot.get_command("config " + opt["command"]).enabled = False
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

    async def format_config(
        self, guild: discord.Guild, key: str, value: str, mention: bool = True
    ) -> str:
        if value is None:
            return None
        config = CONFIG_OPTIONS[key]

        def getname(x):
            return x.mention if mention else x.name

        sep = " " if mention else " | "
        if key == "levelup_channel":
            if value in (None, "none", "any"):
                return str(value).capitalize()
        if config["type"] == "roles":
            value = [value] if isinstance(value, int) else value
            roles = [guild.get_role(x) for x in value]
            roles = [getname(x) for x in roles if x is not None]
            return sep.join(roles)
        if config["type"] == "channels":
            value = [value] if isinstance(value, int) else value
            channels = [guild.get_channel(x) for x in value]
            channels = [getname(x) for x in channels if x is not None]
            return sep.join(channels)
        if config["type"] == "categories":
            value = [value] if isinstance(value, int) else value
            categories = [guild.get_channel(x) for x in value]
            categories = [x.name for x in categories if x is not None]
            return " | ".join(categories)
        if config["type"] == "duration":
            return await self.bot.get_cog("TimeCog").time_delta(
                value, lang="fr", year=True, precision=0
            )
        if config["type"] == "emojis":

            def emojis_convert(
                s_emoji: str, bot_emojis: List[discord.Emoji]
            ) -> Union[str, discord.Emoji]:
                if s_emoji.isnumeric():
                    d_em = discord.utils.get(bot_emojis, id=int(s_emoji))
                    if d_em is None:
                        return ":deleted_emoji:"
                    else:
                        return f":{d_em.name}:"
                return emoji.emojize(s_emoji, language="alias")

            value = [value] if isinstance(value, str) else value
            return " ".join([emojis_convert(x, self.bot.emojis) for x in value])
        if config["type"] == "modlogsFlags":
            flags = self.bot.get_cog("ConfigCog").LogsFlags().intToFlags(value)
            return " - ".join(flags) if len(flags) > 0 else None
        if config["type"] == "language":
            cog = self.bot.get_cog("Languages")
            if cog:
                return cog.languages[value]
            return value
        if config["type"] == "int":
            return value
        return value

    @commands.group(name="config")
    @commands.guild_only()
    @commands.check(checks.is_admin)
    async def main_config(self, ctx: MyContext):
        """Edit your server configuration"""
        if ctx.subcommand_passed is None:
            # get the server config
            config = ctx.bot.server_configs[ctx.guild.id]

            # get the length of the longest key to align the values in columns
            max_key_length = 0
            max_value_length = 0
            for options in self.sorted_options.values():
                configs_len = [len(k) for k in config.keys() if k in options]
                max_key_length = (
                    max(max_key_length, *configs_len)
                    if len(configs_len) > 0
                    else max_key_length
                )
                values_len = [
                    len(str(await self.format_config(ctx.guild, k, v, mention=False)))
                    for k, v in config.items()
                    if k in options
                ]
                max_value_length = (
                    max(max_value_length, *values_len)
                    if len(values_len) > 0
                    else max_value_length
                )
            max_key_length += 3
            max_value_length += 1


            # iterate over modules
            cpt = 0
            embeds = []
            for module, options in sorted(self.sorted_options.items()):

                subconf = {k: v for k, v in config.items() if k in options}
                if len(subconf) == 0:
                    continue

                module_config = ""

                # iterate over configs for that group
                for k, v in subconf.items():
                    value = await self.format_config(ctx.guild, k, v, False)
                    module_config += (f"{k}:").ljust(max_key_length) + f" {value}".ljust(max_value_length) + "\n"

                if hasattr(self.bot.get_cog(module), "_create_config"):
                    for extra in await self.bot.get_cog(module)._create_config(ctx):
                        module_config += (f"[{extra[0]}]").ljust(
                            max_key_length
                        ) + f" {extra[1]}".ljust(max_value_length) + "\n"

                # Put the config in embeds and stack them to be send in group
                embeds.append(
                    discord.Embed(title=module, description=f"```yml\n{module_config}```", colour=0x2F3136)
                )

                cpt += 1

                # Send the config by group of 10 (limit of embed number per message)
                if cpt%10==0:
                    await ctx.send(embeds=embeds)
                    embeds = []
            
            # Send the remaining embeds
            if cpt % 10 != 0:
                await ctx.send(embeds=embeds)

        elif ctx.invoked_subcommand is None:
            await ctx.send(await self.bot._(ctx.guild.id, "sconfig.option-notfound"))

    @main_config.command(name="prefix")
    async def config_prefix(self, ctx: MyContext, new_prefix=None):
        limit = 7
        if new_prefix is not None and len(new_prefix) > limit:
            await ctx.send(
                await self.bot._(ctx.guild.id, "sconfig.prefix-too-long", c=limit)
            )
            return
        await ctx.send(await self.edit_config(ctx.guild.id, "prefix", new_prefix))

    @main_config.command(name="logs_channel")
    async def config_logs_channel(
        self, ctx: MyContext, *, channel: discord.TextChannel
    ):
        await ctx.send(await self.edit_config(ctx.guild.id, "logs_channel", channel.id))
        if logs_cog := self.bot.get_cog("Logs"):
            emb = discord.Embed(
                title=await self.bot._(ctx.guild, "sconfig.config-enabled"),
                description=await self.bot._(
                    ctx.guild, "sconfig.modlogs-channel-enabled"
                ),
                color=16098851,
            )
            await logs_cog.send_embed(ctx.guild, emb)

    # --------------------------------------------------
    # Language
    # --------------------------------------------------

    @main_config.command(name="language", aliases=["lang"])
    async def language(self, ctx: MyContext, lang: str):
        """Change the bot language in your server
        Use the 'list' option to get the available languages"""
        cog = self.bot.get_cog("Languages")
        if not cog:  # if cog not loaded
            await ctx.send("Unable to load languages, please try again later")
        elif lang == "list":  # send a list of available languages
            availabe = " - ".join(cog.languages)
            await ctx.send(
                await self.bot._(ctx.guild.id, "sconfig.languages-list", list=availabe)
            )
        elif lang not in cog.languages:  # invalid language
            await ctx.send(
                await self.bot._(ctx.guild.id, "sconfig.invalid-language", p=ctx.prefix)
            )
        else:  # correct case
            selected = cog.languages.index(lang)
            await ctx.send(await self.edit_config(ctx.guild.id, "language", selected))


async def setup(bot:Gunibot=None, plugin_config:dict=None):
    await bot.add_cog(Sconfig(bot))
