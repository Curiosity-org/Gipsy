"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import io
import os
import sys
import textwrap
import traceback
from contextlib import redirect_stdout

import discord
from discord.ext import commands
from git import Repo, GitCommandError

from utils import Gunibot
from bot import checks
from core import setup_logger


def cleanup_code(content):
    """Automatically removes code blocks from the code."""
    # remove ```py\n```
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:-1])
    # remove `foo`
    return content.strip("` \n")


class Admin(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.logger = setup_logger('admin')
        self._last_result = None

    @commands.group(name="admin", hidden=True)
    @commands.check(checks.is_bot_admin)
    async def main_msg(self, ctx: commands.Context):
        """Commandes réservées aux administrateurs de GuniBot"""
        self.main_msg: commands.Group
        if ctx.subcommand_passed is None:
            text = "Liste des commandes disponibles :"
            for cmd in sorted(self.main_msg.commands, key=lambda x: x.name):
                text += "\n- {} *({})*".format(
                    cmd.name, "..." if cmd.help is None else cmd.help.split("\n")[0]
                )
                if isinstance(cmd, commands.core.Group):
                    for cmds in cmd.commands:
                        text += "\n        - {} *({})*".format(
                            cmds.name, cmds.help.split("\n")[0]
                        )
            await ctx.send(text)

    @main_msg.command(name="pull")
    async def gitpull(self, ctx: commands.Context, branch: str = None):
        """Tire des changements de GitLab"""
        msg = await ctx.send("Mise à jour depuis gitlab...")
        repo = Repo(os.getcwd())
        assert not repo.bare
        if branch:
            try:
                repo.git.checkout(branch)
            except GitCommandError as exc:
                self.logger.exception(exc)
                if (
                    "Your local changes to the following files would be overwritten by checkout"
                    in str(exc)
                ):
                    await msg.edit(
                        content=msg.content + \
                        "\nCertains fichiers ont été modifiés localement - abandon de la procédure"
                    )
                else:
                    await msg.edit(
                        content=msg.content
                        + "\nNom de branche invalide - abandon de la procédure"
                    )
                return
            else:
                await msg.edit(
                    content=msg.content + f"\nBranche {branch} correctement sélectionnée"
                )
        origin = repo.remotes.origin
        origin.pull()
        await self.restart_bot(ctx)

    @main_msg.command(name="branches", aliases=["branch-list"])
    async def git_branches(self, ctx: commands.Context):
        """Montre la liste des branches disponibles"""
        repo = Repo(os.getcwd())
        branches = repo.git.branch("-r").split("\n")
        branches = [x.strip().replace("origin/", "") for x in branches[1:]]
        await ctx.send("Liste des branches : " + " ".join(branches))

    @main_msg.command(name="shutdown")
    async def shutdown(self, ctx: commands.Context):
        """Eteint le bot"""
        msg = await ctx.send("Nettoyage de l'espace de travail...")
        await self.cleanup_workspace()
        await msg.edit(content="Bot en voie d'extinction")
        await self.bot.change_presence(status=discord.Status("offline"))
        self.logger.info("Fermeture du bot")
        await self.bot.close()

    async def cleanup_workspace(self):
        "Delete python cache files"
        for folder_name, _, filenames in os.walk(".."):
            if folder_name.startswith("./env") or folder_name.startswith("./venv"):
                continue
            for filename in filenames:
                if filename.endswith(".pyc"):
                    os.unlink(folder_name + "/" + filename)
            if folder_name.endswith("__pycache__"):
                os.rmdir(folder_name)

    @main_msg.command(name="reboot")
    async def restart_bot(self, ctx: commands.Context):
        """Relance le bot"""
        await ctx.send(content="Redémarrage en cours...")
        await self.cleanup_workspace()
        self.logger.info("Redémarrage du bot")
        os.execl(sys.executable, sys.executable, *sys.argv)

    @main_msg.command(name="purge")
    @commands.guild_only()
    async def clean(self, ctx: commands.Context, limit: int):
        """Enleve <x> messages"""
        if not ctx.bot_permissions.manage_messages:
            await ctx.send("Il me manque la permission de gérer les messages")
        elif not ctx.bot_permissions.read_message_history:
            await ctx.send(
                "Il me manque la permission de lire l'historique des messages"
            )
        else:
            await ctx.message.delete()
            deleted = await ctx.channel.purge(limit=limit)
            await ctx.send(
                f"{len(deleted)} messages supprimés !", delete_after=3.0
            )

    @main_msg.command(name="reload")
    async def reload_cog(self, ctx: commands.Context, *, cog: str):
        """Recharge un module"""
        cogs = cog.split(" ")
        errors_cog = self.bot.get_cog("Errors")
        if len(cogs) == 1 and cogs[0] == "all":
            cogs = sorted([x.file for x in self.bot.cogs.values()])
        reloaded_cogs = []
        for cog in cogs:
            try:
                await self.bot.reload_extension("plugins." + cog + '.' + cog)
            except ModuleNotFoundError:
                await ctx.send(f"Cog {cog} can't be found")
            except commands.errors.ExtensionNotLoaded:
                await ctx.send(f"Cog {cog} was never loaded")
            except Exception as exc: # pylint: disable=broad-exception-caught
                await errors_cog.on_error(exc, ctx)
                await ctx.send(f"**`ERROR:`** {type(exc).__name__} - {exc}")
            else:
                self.logger.info("Module {} rechargé".format(cog))
                reloaded_cogs.append(cog)
        if len(reloaded_cogs) > 0:
            await ctx.bot.get_cog("General").count_lines_code()
            await ctx.send(
                f"These cogs has successfully reloaded: {', '.join(reloaded_cogs)}"
            )

    @main_msg.command(name="add_cog", hidden=True)
    async def add_cog(self, ctx: commands.Context, name: str):
        """Ajouter un cog au bot"""
        try:
            await self.bot.load_extension("plugins." + name)
            await ctx.send("Module '{}' ajouté !".format(name))
            self.logger.info("Module {} ajouté".format(name))
        except Exception as exc:
            await ctx.send(str(exc))

    @main_msg.command(name="del_cog", aliases=["remove_cog"], hidden=True)
    async def rm_cog(self, ctx: commands.Context, name: str):
        """Enlever un cog au bot"""
        try:
            await self.bot.unload_extension("plugins." + name)
            await ctx.send("Module '{}' désactivé !".format(name))
            self.logger.info("Module {} désactivé".format(name))
        except Exception as exc: # pylint: disable=broad-exception-caught
            await ctx.send(str(exc))

    @main_msg.command(name="cogs", hidden=True)
    async def cogs_list(self, ctx: commands.Context):
        """Voir la liste de tout les cogs"""
        text = str()
        for key, value in self.bot.cogs.items():
            text += f"- {value.file if hasattr(value, 'file') else '?'} ({key}) \n"
        await ctx.send(text)

    @main_msg.command(name="activity")
    async def change_activity(self, ctx: commands.Context, action_type: str, *act: str):
        """Change l'activité du bot (play, watch, listen, stream)"""
        act = " ".join(act)
        if action_type in ["game", "play", "playing"]:
            await self.bot.change_presence(activity=discord.Game(name=act))
        elif action_type in ["watch", "see", "watching"]:
            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.watching, name=act)
            )
        elif action_type in ["listen", "listening"]:
            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.listening, name=act)
            )
        elif action_type in ["stream"]:
            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.streaming, name=act)
            )
        else:
            await ctx.send(
                "Sélectionnez *play*, *watch*, *listen* ou *stream* suivi du nom"
            )
        await ctx.message.delete()

    @main_msg.command(name="eval")
    @commands.check(checks.is_bot_admin)
    async def _eval(self, ctx: commands.Context, *, body: str):
        """Evaluates a code
        Credits: Rapptz (https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py)"""
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "_": self._last_result,
        }
        env.update(globals())

        body = cleanup_code(body)
        stdout = io.StringIO()
        try:
            to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'
        except Exception as exc: # pylint: disable=broad-exception-caught
            await self.bot.get_cog("Errors").on_error(exc, ctx)
            return
        try:
            exec(to_compile, env) # pylint: disable=exec-used
        except Exception as exc: # pylint: disable=broad-exception-caught
            return await ctx.send(f"```py\n{exc.__class__.__name__}: {exc}\n```")

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as exc: # pylint: disable=broad-exception-caught
            value = stdout.getvalue()
            await ctx.send(f"```py\n{value}{traceback.format_exc()}\n```")
        else:
            value = stdout.getvalue()

            if ret is None:
                if value:
                    await ctx.send(f"```py\n{value}\n```")
            else:
                self._last_result = ret
                await ctx.send(f"```py\n{value}{ret}\n```")

async def setup(bot:Gunibot):
    await bot.add_cog(Admin(bot), icon="🚨")
