import discord
import sys
import traceback
import random
import re
from discord.ext import commands


class Errors(commands.Cog):
    """General cog for error management."""

    def __init__(self, bot):
        self.bot = bot
        self.file = "errors"

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command."""
        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        ignored = (commands.errors.CommandNotFound, commands.errors.CheckFailure,
                   commands.errors.ConversionError, discord.errors.Forbidden)
        actually_not_ignored = (commands.errors.NoPrivateMessage)

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored) and not isinstance(error, actually_not_ignored):
            return
        elif isinstance(error, commands.errors.CommandOnCooldown):
            if await self.bot.cogs['Admin'].check_if_admin(ctx):
                await ctx.reinvoke()
                return
            await ctx.send("Vous êtes en cooldown pour cette commande. Veuillez attendre encore {} secondes...".format(round(error.retry_after, 2)))
            return
        elif isinstance(error, (commands.BadArgument, commands.BadUnionArgument)):
            raw_error = str(error).replace(
                '@eveyrone', '@​everyone').replace('@here', '@​here')
            # Could not convert "limit" into int. OR Converting to "int" failed for parameter "number".
            r = re.search(
                r'Could not convert \"(?P<arg>[^\"]+)\" into (?P<type>[^.\n]+)', raw_error)
            if r is None:
                r = re.search(
                    r'Converting to \"(?P<type>[^\"]+)\" failed for parameter \"(?P<arg>[^.\n]+)\"', raw_error)
            if r is not None:
                return await ctx.send("Oups, impossible de convertir le paramètre `{p}` en type \"{t}\" :confused:".format(p=r.group('arg'), t=r.group('type')))
            # zzz is not a recognised boolean option
            r = re.search(
                r'(?P<arg>[^\"]+) is not a recognised (?P<type>[^.\n]+) option', raw_error)
            if r is not None:
                return await ctx.send("`{p}` n'est pas de type {t}".format(p=r.group('arg'), t=r.group('type')))
            # Member "Z_runner" not found
            r = re.search(r'Member \"([^\"]+)\" not found', raw_error)
            if r is not None:
                return await ctx.send("Impossible de trouver le membre `{}` :confused:".format(r.group(1)))
            # User "Z_runner" not found
            r = re.search(r'User \"([^\"]+)\" not found', raw_error)
            if r is not None:
                return await ctx.send("Impossible de trouver l'utilisateur `{}` :confused:".format(r.group(1)))
            # Role "Admin" not found
            r = re.search(r'Role \"([^\"]+)\" not found', raw_error)
            if r is not None:
                return await ctx.send("Impossible de trouver le rôle `{}`".format(r.group(1)))
            # Emoji ":shock:" not found
            r = re.search(r'Emoji \"([^\"]+)\" not found', raw_error)
            if r is not None:
                return await ctx.send("Emoji `{}` introuvable".format(r.group(1)))
             # Colour "blue" is invalid
            r = re.search(r'Colour \"([^\"]+)\" is invalid', raw_error)
            if r is not None:
                return await ctx.send("La couleur `{}` est invalide".format(r.group(1)))
            # Channel "twitter" not found.
            r = re.search(r'Channel \"([^\"]+)\" not found', raw_error)
            if r is not None:
                return await ctx.send("Le salon {} est introuvable".format(r.group(1)))
            # Message "1243" not found.
            r = re.search(r'Message \"([^\"]+)\" not found', raw_error)
            if r is not None:
                return await ctx.send("Message introuvable")
            # Too many text channels
            if raw_error == 'Too many text channels':
                return await ctx.send("Vous avez trop de salons textuels accessibles")
            # Invalid duration: 2d
            r = re.search(r'Invalid duration: ([^\" ]+)', raw_error)
            if r is not None:
                return await ctx.send("La durée `{}` est invalide".format(r.group(1)))
            # Invalid invite: nope
            r = re.search(r'Invalid invite: (\S+)', raw_error)
            if r is not None:
                return await ctx.send("Invitation de bot ou de serveur invalide")
            # Invalid guild: test
            r = re.search(r'Invalid guild: (\S+)', raw_error)
            if r is not None:
                return await ctx.send("Ce serveur est introuvable")
            # Invalid url: nou
            r = re.search(r'Invalid url: (\S+)', raw_error)
            if r is not None:
                return await ctx.send("Url invalide")
            # Invalid emoji: lmao
            r = re.search(r'Invalid emoji: (\S+)', raw_error)
            if r is not None:
                return await ctx.send("Emoji invalide")
            print('errors -', error)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Oups, il manque l'argument \"{}\"".format(error.param.name))
            return
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("La commande {} est désactivée".format(ctx.invoked_with))
            return
        elif isinstance(error, commands.errors.NoPrivateMessage):
            await ctx.send("Cette commande est indisponible en Messages Privés")
            return
        else:
            try:
                raw_error = str(error).replace(
                    '@eveyrone', '@​everyone').replace('@here', '@​here')
                await ctx.send("`ERROR:` {}".format(raw_error))
            except Exception as newerror:
                self.bot.log.info("[on_cmd_error] Can't send error on channel {}: {}".format(
                    ctx.channel.id, newerror))
        # All other Errors not returned come here... And we can just print the default TraceBack.
        self.bot.log.warning(
            'Ignoring exception in command {}:'.format(ctx.message.content))
        await self.on_error(error, ctx)

    @commands.Cog.listener()
    async def on_error(self, error, ctx=None):
        try:
            if isinstance(ctx, discord.Message):
                ctx = await self.bot.get_context(ctx)
            tr = traceback.format_exception(
                type(error), error, error.__traceback__)
            msg = "```python\n{}\n```".format(" ".join(tr))
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
        try:
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr)
        except Exception as e:
            self.bot.log.warning(f"[on_error] {e}", exc_info=True)

    async def senf_err_msg(self, msg):
        """Envoie un message dans le salon d'erreur"""
        salon = self.bot.get_channel(self.bot.config["errors_channel"])
        if salon is None:
            return False
        await salon.send(msg)
        return True


def setup(bot):
    bot.add_cog(Errors(bot))
