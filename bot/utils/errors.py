"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import re
import traceback

import discord
from discord.ext import commands

from utils import CheckException, Gunibot, MyContext
from bot import checks
from core import config


class Errors(commands.Cog):
    """General cog for error management."""

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "errors"

    @commands.Cog.listener()
    async def on_command_error(self, ctx: MyContext, error: Exception):
        """The event triggered when an error is raised while invoking a command."""
        # This prevents any commands with local handlers being handled here in
        # on_command_error.
        if hasattr(ctx.command, "on_error"):
            return

        ignored = (
            commands.errors.CommandNotFound,
            commands.errors.CheckFailure,
            commands.errors.ConversionError,
            discord.errors.Forbidden,
        )
        actually_not_ignored = commands.errors.NoPrivateMessage

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to
        # on_command_error.
        error = getattr(error, "original", error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored) and not isinstance(error, actually_not_ignored):
            return
        elif isinstance(error, commands.errors.CommandOnCooldown):
            if checks.is_bot_admin(ctx):
                await ctx.reinvoke()
                return
            await ctx.send(
                await self.bot._(
                    ctx.channel, "errors.cooldown", c=round(error.retry_after, 2)
                ),
                ephemeral=True,
            )
            return
        elif isinstance(error, CheckException):
            return await ctx.send(
                await self.bot._(ctx.channel, "errors.custom_checks." + error.id),
                ephemeral=True,
            )
        elif isinstance(error, (commands.BadArgument, commands.BadUnionArgument)):
            raw_error = str(error)
            if raw_error == "Unknown argument":
                return await ctx.send(
                    await self.bot._(ctx.channel, "errors.unknown-arg"), ephemeral=True
                )
            elif raw_error == "Unknown dependency action type":
                return await ctx.send(
                    await self.bot._(ctx.channel, "errors.invalid-dependency"),
                    ephemeral=True,
                )
            elif raw_error == "Unknown dependency trigger type":
                return await ctx.send(
                    await self.bot._(ctx.channel, "errors.invalid-trigger"),
                    ephemeral=True,
                )
            elif raw_error == "Unknown permission type":
                return await ctx.send(
                    await self.bot._(ctx.channel, "errors.invalid-permission"),
                    ephemeral=True,
                )
            # Could not convert "limit" into int. OR Converting to "int" failed
            # for parameter "number".
            result = re.search(
                r"Could not convert \"(?P<arg>[^\"]+)\" into (?P<type>[^.\n]+)",
                raw_error,
            )
            if result is None:
                result = re.search(
                    r"Converting to \"(?P<type>[^\"]+)\" failed for parameter \"(?P<arg>[^.\n]+)\"",
                    raw_error,
                )
            if result is not None:
                return await ctx.send(
                    await self.bot._(
                        ctx.channel,
                        "errors.unknown-arg",
                        p=result.group("arg"),
                        t=result.group("type"),
                    )
                )
            # zzz is not a recognised boolean option
            result = re.search(
                r"(?P<arg>[^\"]+) is not a recognised (?P<type>[^.\n]+) option",
                raw_error,
            )
            if result is not None:
                return await ctx.send(
                    await self.bot._(
                        ctx.channel,
                        "errors.invalid-type",
                        p=result.group("arg"),
                        t=result.group("type"),
                    ),
                    ephemeral=True,
                )
            # Member "Z_runner" not found
            result = re.search(r"Member \"([^\"]+)\" not found", raw_error)
            if result is not None:
                return await ctx.send(
                    await self.bot._(
                        ctx.channel, "errors.unknown-member", m=result.group(1)
                    ),
                    ephemeral=True,
                )
            # User "Z_runner" not found
            result = re.search(r"User \"([^\"]+)\" not found", raw_error)
            if result is not None:
                return await ctx.send(
                    await self.bot._(
                        ctx.channel, "errors.unknown-user", u=result.group(1)
                    ),
                    ephemeral=True,
                )
            # Role "Admin" not found
            result = re.search(r"Role \"([^\"]+)\" not found", raw_error)
            if result is not None:
                return await ctx.send(
                    await self.bot._(
                        ctx.channel, "errors.unknown-role", r=result.group(1)
                    ),
                    ephemeral=True,
                )
            # Emoji ":shock:" not found
            result = re.search(r"Emoji \"([^\"]+)\" not found", raw_error)
            if result is not None:
                return await ctx.send(
                    await self.bot._(
                        ctx.channel, "errors.unknown-emoji", e=result.group(1)
                    ),
                    ephemeral=True,
                )
            # Colour "blue" is invalid
            result = re.search(r"Colour \"([^\"]+)\" is invalid", raw_error)
            if result is not None:
                return await ctx.send(
                    await self.bot._(
                        ctx.channel, "errors.invalid-color", c=result.group(1)
                    ),
                    ephemeral=True,
                )
            # Channel "twitter" not found.
            result = re.search(r"Channel \"([^\"]+)\" not found", raw_error)
            if result is not None:
                return await ctx.send(
                    await self.bot._(
                        ctx.channel, "errors.unknown-channel", c=result.group(1)
                    ),
                    ephemeral=True,
                )
            # Message "1243" not found.
            result = re.search(r"Message \"([^\"]+)\" not found", raw_error)
            if result is not None:
                return await ctx.send(
                    await self.bot._(
                        ctx.channel, "errors.unknown-message", m=result.group(1)
                    ),
                    ephemeral=True,
                )
            # Too many text channels
            if raw_error == "Too many text channels":
                return await ctx.send(
                    await self.bot._(ctx.channel, "errors.too-many-text-channels"),
                    ephemeral=True,
                )
            # Invalid duration: 2d
            result = re.search(r"Invalid duration: ([^\" ]+)", raw_error)
            if result is not None:
                return await ctx.send(
                    await self.bot._(
                        ctx.channel,
                        "errors.invalid-duration",
                        d=result.group(1),
                    ),
                    ephemeral=True,
                )
            # Invalid invite: nope
            result = re.search(r"Invalid invite: (\S+)", raw_error)
            if result is not None:
                return await ctx.send(
                    await self.bot._(ctx.channel, "errors.invalid-invite"),
                    ephemeral=True,
                )
            # Invalid guild: test
            result = re.search(r"Invalid guild: (\S+)", raw_error)
            if result is not None:
                return await ctx.send(
                    await self.bot._(ctx.channel, "errors.unknown-server"),
                    ephemeral=True,
                )
            # Invalid url: nou
            result = re.search(r"Invalid url: (\S+)", raw_error)
            if result is not None:
                return await ctx.send(
                    await self.bot._(ctx.channel, "errors.invalid-url"), ephemeral=True
                )
            # Invalid emoji: lmao
            result = re.search(r"Invalid emoji: (\S+)", raw_error)
            if result is not None:
                return await ctx.send(
                    await self.bot._(ctx.channel, "errors.invalid-emoji"),
                    ephemeral=True,
                )
            print("errors -", error)
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                await self.bot._(ctx.channel, "errors.missing-arg", a=error.param.name),
                ephemeral=True,
            )
            return
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(
                await self.bot._(
                    ctx.channel, "errors.disabled-cmd", c=ctx.invoked_with
                ),
                ephemeral=True,
            )
            return
        elif isinstance(error, commands.errors.NoPrivateMessage):
            await ctx.send(
                await self.bot._(ctx.channel, "errors.disabled-dm"), ephemeral=True
            )
            return
        else:
            await ctx.send(
                await self.bot._(ctx.channel, "errors.error-unknown"), ephemeral=True
            )
        # All other Errors not returned come here... And we can just print the
        # default TraceBack.
        self.bot.log.warning(
            f"Ignoring exception in command {ctx.message.content}:",
            exc_info=(type(error), error, error.__traceback__),
        )
        await self.on_error(error, ctx)

    @commands.Cog.listener()
    async def on_error(self, error, ctx=None):
        try:
            if isinstance(ctx, discord.Message):
                ctx = await self.bot.get_context(ctx)
            trace = traceback.format_exception(type(error), error, error.__traceback__)
            msg = f"```python\n{' '.join(trace)[:1900]}\n```"
            if ctx is None:
                await self.senf_err_msg(f"Internal Error\n{msg}")
            elif ctx.guild is None:
                await self.senf_err_msg(f"DM | {ctx.channel.recipient.name}\n{msg}")
            elif ctx.channel.id == 698547216155017236:
                return await ctx.send(msg)
            else:
                await self.senf_err_msg(
                    ctx.guild.name + " | " + ctx.channel.name + "\n" + msg
                )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.bot.log.warning(f"[on_error] {exc}", exc_info=True)

    async def senf_err_msg(self, msg):
        """Sends a message to the error channel"""
        channel = self.bot.get_channel(config.get("bot.error_channels"))
        if channel is None:
            return False
        await channel.send(msg)
        return True


async def setup(bot: Gunibot = None):
    await bot.add_cog(Errors(bot))
