import inspect
import itertools
import typing
from typing import Any, List, Optional, Union

import nextcord
from nextcord.ext import commands
from utils import Gunibot, MyContext


class Help(commands.HelpCommand):
    ANNOTATION_TRANSLATION = {
        nextcord.User: "annotation.user",
        nextcord.Member: "annotation.user",
        nextcord.TextChannel: "annotation.textchannel",
        nextcord.VoiceChannel: "annotation.voicechannel",
        nextcord.Role: "annotation.role",
        nextcord.Guild: "annotation.guild",
        str: "annotation.string",
        int: "annotation.int",
        bool: "annotation.bool",
        False: "annotation.bool",
        True: "annotation.bool",
        nextcord.Message: "annotation.message",
    }

    DEFAULT_TRANSLATION = {
        True: "help_default.true_",
        False: "help_default.false_",
    }

    embed: nextcord.Embed

    context: MyContext

    async def get_help_embed(self, *args, **kwargs) -> nextcord.Embed:
        """Returns the embed formated for help message
        The color of the embed is set by default, as well as the author.

        Attributes
        ----------
        You can put parameters for the :class:`nextcord.Embed` constructor method

        Returns
        -------
        :class:`nextcord.Embed`
            The help embed
        """

        #load the config options
        color = self.context.bot.config.get("help_embed_color", 0)
        author = self.context.bot.config.get("help_author").format(user=self.context.bot.user)
        icon_url = self.context.bot.config.get("help_author_icon_url").format(user=self.context.bot.user)

        embed = nextcord.Embed(
            *args, **kwargs,
            color=color
        )

        embed.set_author(
            name=author,
            icon_url=icon_url
        )
        embed.set_footer(
            text=await self.context.bot._(self.context, "help.help-tip", prefix=self.context.clean_prefix)
        )
        
        return embed

    async def get_bot_command_formating(self, commands_: List[commands.Command]) -> str:
        """Returns a string representing `commands_`
        
        Attributes
        ----------
        commands_: List[:class:`nextcord.ext.commands.Command`]
            The commands fro which to return the string representation
        
        Returns
        -------
        :class:`str`
            The string representation of the commands
        """
        output = ''
        for command in commands_:
            output += await self.get_command_list_string(command)
            output += "\n"
        return output

    async def get_type_string(self, type: Any) -> Optional[str]:
        """Returns the string representation of a type
        (like nextcord.Message, etc...)

        Attributes
        ----------
        type: Any
            The type for which to return the string representation
        
        Returns
        -------
        Optional[:class:`str`]
            The string representation
            If not translation is found, it return None
        """
        if type in self.ANNOTATION_TRANSLATION:
            return await self.context.bot._(self.context, self.ANNOTATION_TRANSLATION[type])
    
    async def get_annotation_type_string(self, parameter: inspect.Parameter) -> Optional[str]:
        """Returns the string representation of type annotation in parameter
        
        Attributes
        ----------
        annotation: :class:`inspect.Parameter`
            The annotation for which to return the type string representation
        
        Returns
        -------
        Optional[:class:`str`]
            The string representation
            If no translation can be found, it returns None
        """
        type_str  = await self.get_type_string(parameter.annotation)
        if type_str is None:
            return await self.get_type_string(parameter.default)
        else:
            return type_str
    
    async def get_parameter_string(self, parameter: inspect.Parameter) -> str:
        """Returns the string representation of a command parameter
        
        Attributes
        ----------
        parameter: :class:`inspect.Parameter`
            The parameter for which to return the string representation
        
        Returns
        -------
        :class:`str`
            The string representation of the parameter
        """
        annotation = parameter.annotation
        types = []
        if type(annotation) == commands.Greedy:
            type_ = await self.get_type_string(annotation.converter)
            if type_ is not None:
                types.append(
                    await self.context.bot._(self.context, "help.greedy", type=type_)
                )
        elif type(annotation) == typing._UnionGenericAlias:
            for arg in annotation.__args__:
                type_ = await self.get_type_string(arg)
                if type_ != None:
                    types.append(type_)
        else:
            type_ = await self.get_annotation_type_string(parameter)
            if type_ is not None:
                types.append(type_)
        return ", ".join(types) if len(types) > 0 else None

    
    async def get_parameters_string(self, command: commands.Command, sep="\n") -> Optional[str]:
        """Returns the string representing all command parameters
        
        Attributes
        ----------
        command: :class:`nextcord.ext.commands.Command`
            The command for which to get the parameters string representation
        sep: :class:`str`
            The separator to put between parameters
        
        Returns
        -------
        Optional[:class:`str`]
            The string representation of command parameter
            If the command has no parameters, the function returns None
        """
        bot: Gunibot = self.context.bot
        result = ""

        for name, parameter in command.clean_params.items():
            type = await self.get_parameter_string(parameter)
            if type is not None:
                type = await bot._(self.context, "help.type", type=type)
            else:
                type = ""
            
            if parameter.default and parameter.default != inspect._empty: #parse default
                if parameter.default in self.DEFAULT_TRANSLATION:
                    default = await bot._(self.context, self.DEFAULT_TRANSLATION[parameter.default])
                    default = await bot._(self.context, "help.default", default=default)
                else:
                    default = await bot._(self.context, "help.default", default=repr(parameter.default))
            else:
                default = ""
            
            result += f"**{name}**{type}{default}"
            result += sep #add end separator

        return result if len(result) > 0 else None
    
    async def get_command_list_string(self, command: commands.Command) -> str:
        """Returns a string representing `command` in a list of commands
        
        Attributes
        ----------
        command: :class:`nextcord.ext.commands.Command`
            The command for which to return the representation
        
        Returns
        -------
        :class:`str`
            The string representation of `command`
        """
        name = f"• **{command.name}**"
        if command.short_doc:
            short_doc = await self.context.bot._(self.context, "help.short_doc", short_doc=command.short_doc[:40]+("…" if len(command.short_doc)>40 else ""))
        else:
            short_doc = ""

        return name+short_doc
    
    async def get_subcommand_string(self, group: Union[commands.Group, commands.Cog], sep="\n") -> Optional[str]:
        """Returns the string representing all group subcommands
        
        Attributes
        ----------
        group: :class:`nextcord.ext.commands.Group`
            The group for which to get the subcommand string representation
        sep: :class:`str`
            The separator to put between subcommands
        
        Returns
        -------
        Optional[:class:`str`]
            The string representation of group subcommands
            If the group has no subcommand, the function returns None
        """
        bot: Gunibot = self.context.bot
        result = ""
        
        if type(group) == commands.Group:
            commands_ = sorted(group.commands, key=lambda command: command.name)
        elif issubclass(type(group), commands.Cog):
            commands_ = sorted(group.get_commands(), key=lambda command: command.name)

        for command in commands_:
            result += await self.get_command_list_string(command)
            result += sep
        
        if len(result) > 1024:
            result = "**"
            for command in commands_:
                result += f"• {command.name}"
                result += sep
            result += "**"
            if len(result) > 1024:
                result = result[:1023] + "…"

        return result if len(result) > 0 else None
    
    async def add_aliases(self, command: Union[commands.Command, commands.Group]):
        """Add the alias field in the embed if necessary

        Parameters
        ----------
        command: Union[:class:`commands.Command`, :class:`commands.Group`]
            The command for which to check the aliases
        """
        
        if len(command.aliases) > 0:
            aliases = '`'+"`, `".join(command.aliases+[command.name])+'`'
            self.embed.add_field(
                name=await self.context.bot._(self.context, "help.alias"),
                value=aliases,
                inline=False
            )
        
    async def add_parameters(self, command: Union[commands.Command, commands.Group]):
        """Add the parameters field in the embed if necessary

        Parameters
        ----------
        command: Union[:class:`commands.Command`, :class:`commands.Group`]
            The command for which to check the parameters
        """
        parameters = await self.get_parameters_string(command)
        if parameters is not None:
            self.embed.add_field(
                name=await self.context.bot._(self.context, "help.parameters"),
                value=parameters,
                inline=False
            )
        
    async def add_subcommands(self, group: Union[commands.Group, commands.Cog]):
        """Add the subcommands field in the embed if necessary

        Parameters
        ----------
        command: Union[:class:`commands.Command`, :class:`commands.Group`]
            The command for which to check the subcommands
        """
        subcommands = await self.get_subcommand_string(group)
        if subcommands is not None:
            self.embed.add_field(
                name=await self.context.bot._(self.context, "help.subcommands"),
                value=subcommands,
                inline=False
            )

    async def send_bot_help(self, mapping) -> None:
        """Send the help message for the bot in the context channel"""
        ctx = self.context
        bot: Gunibot = ctx.bot

        self.embed = await self.get_help_embed(
            title=await bot._(ctx, "help.bot-help-title")
        )

        if bot.description:
            self.embed.description = f"```\n{bot.description}```"
        
        no_category = await bot._(ctx, "help.no-category")
        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name if cog is not None else no_category
        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        to_iterate = itertools.groupby(filtered, key=get_category)

        for category, commands_ in to_iterate:
            commands_ = sorted(commands_, key=lambda c: c.name)
            self.embed.add_field(
                name=f"{category}",
                value=await self.get_bot_command_formating(commands_),
                inline=False
            )
        
        await ctx.send(embed=self.embed)
    
    async def send_command_help(self, command: commands.Command) -> None:
        """Send the help message for command in the context channel
        
        Attributes
        ----------
        command: :class:`nextcord.ext.commands.Command`
            The command for which to send the help
        """
        ctx = self.context
        bot: Gunibot = ctx.bot
        self.embed = await self.get_help_embed(
            title = await bot._(ctx, "help.command-help-title", name=command.name)
        )

        description = "```\n" #include signature and description in the same code field
        description += await bot._(ctx, "help.help-signature-format", signature=self.get_command_signature(command))

        if command.help != "":
            description += f"\n{command.help}"
        description += "```"
        
        self.embed.description = description

        await self.add_parameters(command)
        
        await self.add_aliases(command)

        await ctx.send(embed=self.embed)
    
    async def send_group_help(self, group: commands.Group) -> None:
        """Send the help message for a group in the context channel
        
        Attributes
        ----------
        group: :class:`nextcord.ext.commands.Group`
            The command for which to send the help
        """
        ctx = self.context
        bot: Gunibot = ctx.bot

        self.embed = await self.get_help_embed(
            title = await bot._(ctx, "help.group-help-title", name=group.name)
        )

        description = "```\n" #include signature and description in the same code field
        description += await bot._(ctx, "help.help-signature-format", signature=self.get_command_signature(group))

        if group.help != "":
            description += f"\n{group.help}"
        description += "```"

        self.embed.description = description

        await self.add_parameters(group)
        
        await self.add_subcommands(group)
        
        await self.add_aliases(group)

        await ctx.send(embed=self.embed)
    
    async def send_cog_help(self, cog: commands.Cog) -> None:
        """Send the help message for the cog in the context channel
        
        Attributes
        ----------
        cog: :class:`nextcord.ext.commands.Cog`
            The cog for which to send the help
        """
        ctx = self.context
        bot: Gunibot = ctx.bot

        self.embed = await self.get_help_embed(
            title = await bot._(ctx, "help.cog-help-title", name=cog.qualified_name)
        )

        description = ""

        if cog.description != "":
            description += f"\n```\n{cog.description}```"

        self.embed.description = description
        
        await self.add_subcommands(cog)

        await ctx.send(embed=self.embed)
    
    async def command_not_found(self, command: str) -> str:
        """Return the string for command not found error
        
        Attributes
        ----------
        command: :class:`str`
            The command name
        """
        return await self.context.bot._(self.context, "help.not-found", command=command)
    
    async def send_error_message(self, error: str) -> None:
        """Raise the help error message in context channel
        
        Attributes
        ----------
        error: :class:`str`
            The error to raise
        """
        ctx = self.context
        bot: Gunibot = ctx.bot

        self.embed = await self.get_help_embed(
            title=error
        )

        await ctx.send(embed=self.embed)


class HelpCog(commands.Cog):

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "help"
        self.config_options = ["help_embed_color", "help_author", "help_author_icon_url"]
        bot.get_command("config").add_command(self.help_embed_color)
        bot.get_command("config").add_command(self.help_author)
        bot.get_command("config").add_command(self.help_author_icon_url)
    
    @commands.command(name="help_embed_color")
    @commands.guild_only()
    async def help_embed_color(self, ctx: MyContext, color: nextcord.Color):
        """Edit the help embed color"""
        # save result
        await ctx.send(await self.bot.sconfig.edit_config(ctx.guild.id, "help_embed_color", color.value))
    
    @commands.command(name="help_author")
    @commands.guild_only()
    async def help_author(self, ctx: MyContext, *, text: str):
        """Edit the help embed author text"""
        if len(text) > 250:
            await ctx.send("Your text can't be longer than 250 characters")
            return
        await ctx.send(await self.bot.sconfig.edit_config(ctx.guild.id, "help_author", text))
    
    @commands.command(name="help_author_icon_url")
    @commands.guild_only()
    async def help_author_icon_url(self, ctx: MyContext, url: str):
        await ctx.send(await self.bot.sconfig.edit_config(ctx.guild.id, "help_author_icon_url", url))


def setup(bot: Gunibot):
    bot.help_command = Help()
    bot.add_cog(HelpCog(bot))

def teardown(bot: Gunibot):
    bot.help_command = commands.DefaultHelpCommand()
    bot.remove_cog("HelpCog")
