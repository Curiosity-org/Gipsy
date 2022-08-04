import re
import traceback

import sys
sys.path.append("./bot")
import checks
import nextcord
from nextcord.ext import commands
from utils import CheckException, Gunibot, MyContext


class Errors(commands.Cog):
    """General cog for error management."""

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "errors"

    @commands.Cog.listener()
    async def on_command_error(self, ctx: MyContext, error: Exception):
        """The event triggered when an error is raised while invoking a command."""
        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        ignored = (commands.errors.CommandNotFound, commands.errors.CheckFailure,
                   commands.errors.ConversionError, nextcord.errors.Forbidden)
        actually_not_ignored = (commands.errors.NoPrivateMessage)

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored) and not isinstance(error, actually_not_ignored):
            return
        elif isinstance(error, commands.errors.CommandOnCooldown):
            if checks.is_bot_admin(ctx):
                await ctx.reinvoke()
                return
            await ctx.send(await self.bot._(ctx.channel, "errors.cooldown", c=round(error.retry_after, 2)))
            return
        elif isinstance(error, CheckException):
            return await ctx.send(await self.bot._(ctx.channel, "errors.custom_checks."+error.id))
        elif isinstance(error, (commands.BadArgument, commands.BadUnionArgument)):
            raw_error = str(error)
            if raw_error == "Unknown argument":
                return await ctx.send(await self.bot._(ctx.channel, "errors.unknown-arg"))
            elif raw_error == "Unknown dependency action type":
                return await ctx.send(await self.bot._(ctx.channel, "errors.invalid-dependency"))
            elif raw_error == "Unknown dependency trigger type":
                return await ctx.send(await self.bot._(ctx.channel, "errors.invalid-trigger"))
            elif raw_error == "Unknown permission type":
                return await ctx.send(await self.bot._(ctx.channel, "errors.invalid-permission"))
            # Could not convert "limit" into int. OR Converting to "int" failed for parameter "number".
            r = re.search(
                r'Could not convert \"(?P<arg>[^\"]+)\" into (?P<type>[^.\n]+)', raw_error)
            if r is None:
                r = re.search(
                    r'Converting to \"(?P<type>[^\"]+)\" failed for parameter \"(?P<arg>[^.\n]+)\"', raw_error)
            if r is not None:
                return await ctx.send(await self.bot._(ctx.channel, "errors.unknown-arg", p=r.group('arg'), t=r.group('type')))
            # zzz is not a recognised boolean option
            r = re.search(
                r'(?P<arg>[^\"]+) is not a recognised (?P<type>[^.\n]+) option', raw_error)
            if r is not None:
                return await ctx.send(await self.bot._(ctx.channel, "errors.invalid-type", p=r.group('arg'), t=r.group('type')))
            # Member "Z_runner" not found
            r = re.search(r'Member \"([^\"]+)\" not found', raw_error)
            if r is not None:
                return await ctx.send(await self.bot._(ctx.channel, "errors.unknown-member", m=r.group(1)))
            # User "Z_runner" not found
            r = re.search(r'User \"([^\"]+)\" not found', raw_error)
            if r is not None:
                return await ctx.send(await self.bot._(ctx.channel, "errors.unknown-user", u=r.group(1)))
            # Role "Admin" not found
            r = re.search(r'Role \"([^\"]+)\" not found', raw_error)
            if r is not None:
                return await ctx.send(await self.bot._(ctx.channel, "errors.unknown-role", r=r.group(1)))
            # Emoji ":shock:" not found
            r = re.search(r'Emoji \"([^\"]+)\" not found', raw_error)
            if r is not None:
                return await ctx.send(await self.bot._(ctx.channel, "errors.unknown-emoji", e=r.group(1)))
             # Colour "blue" is invalid
            r = re.search(r'Colour \"([^\"]+)\" is invalid', raw_error)
            if r is not None:
                return await ctx.send(await self.bot._(ctx.channel, "errors.invalid-color", c=r.group(1)))
            # Channel "twitter" not found.
            r = re.search(r'Channel \"([^\"]+)\" not found', raw_error)
            if r is not None:
                return await ctx.send(await self.bot._(ctx.channel, "errors.unknown-channel", c=r.group(1)))
            # Message "1243" not found.
            r = re.search(r'Message \"([^\"]+)\" not found', raw_error)
            if r is not None:
                return await ctx.send(await self.bot._(ctx.channel, "errors.unknown-message", m=r.group(1)))
            # Group "twitter" not found.
            r = re.search(r'Group \"([^\"]+)\" not found', raw_error)
            if r is not None:
                return await ctx.send(await self.bot._(ctx.channel, "errors.unknown-group", g=r.group(1)))
            # Too many text channels
            if raw_error == 'Too many text channels':
                return await ctx.send(await self.bot._(ctx.channel, "errors.too-many-text-channels"))
            # Invalid duration: 2d
            r = re.search(r'Invalid duration: ([^\" ]+)', raw_error)
            if r is not None:
                return await ctx.send(await self.bot._(ctx.channel, "errors.invalid-duration", d=r.group(1)))
            # Invalid invite: nope
            r = re.search(r'Invalid invite: (\S+)', raw_error)
            if r is not None:
                return await ctx.send(await self.bot._(ctx.channel, "errors.invalid-invite"))
            # Invalid guild: test
            r = re.search(r'Invalid guild: (\S+)', raw_error)
            if r is not None:
                return await ctx.send(await self.bot._(ctx.channel, "errors.unknown-server"))
            # Invalid url: nou
            r = re.search(r'Invalid url: (\S+)', raw_error)
            if r is not None:
                return await ctx.send(await self.bot._(ctx.channel, "errors.invalid-url"))
            # Invalid emoji: lmao
            r = re.search(r'Invalid emoji: (\S+)', raw_error)
            if r is not None:
                return await ctx.send(await self.bot._(ctx.channel, "errors.invalid-emoji"))
            print('errors -', error)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(await self.bot._(ctx.channel, "errors.missing-arg", a=error.param.name))
            return
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(await self.bot._(ctx.channel, "errors.disabled-cmd", c=ctx.invoked_with))
            return
        elif isinstance(error, commands.errors.NoPrivateMessage):
            await ctx.send(await self.bot._(ctx.channel, "errors.disabled-dm"))
            return
        else:
            await ctx.send(await self.bot._(ctx.channel, "errors.error-unknown"))
        # All other Errors not returned come here... And we can just print the default TraceBack.
        self.bot.log.warning('Ignoring exception in command {}:'.format(
            ctx.message.content), exc_info=(type(error), error, error.__traceback__))
        await self.on_error(error, ctx)

    @commands.Cog.listener()
    async def on_error(self, error, ctx=None):
        try:
            if isinstance(ctx, nextcord.Message):
                ctx = await self.bot.get_context(ctx)
            tr = traceback.format_exception(
                type(error), error, error.__traceback__)
            msg = "```python\n{}\n```".format(" ".join(tr)[:1900])
            if ctx is None:
                await self.senf_err_msg(f"Internal Error\n{msg}")
            elif ctx.guild is None:
                await self.senf_err_msg(f"DM | {ctx.channel.recipient.name}\n{msg}")
            elif ctx.channel.id == 698547216155017236:
                return await ctx.send(msg)
            else:
                await self.senf_err_msg(ctx.guild.name+" | "+ctx.channel.name+"\n"+msg)
        except Exception as e:
            self.bot.log.warn(f"[on_error] {e}", exc_info=True)

    async def senf_err_msg(self, msg):
        """Sends a message to the error channel"""
        salon = self.bot.get_channel(self.bot.config["errors_channel"])
        if salon is None:
            return False
        await salon.send(msg)
        return True


def setup(bot):
    bot.add_cog(Errors(bot))
